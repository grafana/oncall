from functools import partial
from uuid import uuid4

from celery.exceptions import Retry
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from kombu.utils.uuid import uuid as celery_uuid
from telegram.error import RetryAfter

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.base.messaging import get_messaging_backend_from_id
from apps.metrics_exporter.tasks import update_metrics_for_user
from apps.phone_notifications.phone_backend import PhoneBackend
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


def create_send_bundled_notification_task(user_notification_bundle, alert_group, task_id, eta):
    """Schedule notification task for bundled notifications"""
    send_bundled_notification.apply_async(
        (user_notification_bundle.id,),
        eta=eta,
        task_id=task_id,
    )
    task_logger.info(
        f"Scheduled send_bundled_notification task {task_id}, "
        f"user_notification_bundle: {user_notification_bundle.id}, alert_group {alert_group.id}, eta: {eta}"
    )


def create_perform_notification_task(log_record_pk, alert_group_pk):
    task = perform_notification.apply_async((log_record_pk,))
    task_logger.info(
        f"Created perform_notification task {task} log_record={log_record_pk} " f"alert_group={alert_group_pk}"
    )


def build_user_notification_plan(notification_policy, reason):
    from apps.base.models import UserNotificationPolicy

    # Here we collect a brief overview of notification steps configured for user to send it to thread.
    collected_steps_ids = []
    next_notification_policy = notification_policy.next()
    while next_notification_policy is not None:
        if next_notification_policy.step == UserNotificationPolicy.Step.NOTIFY:
            if next_notification_policy.notify_by not in collected_steps_ids:
                collected_steps_ids.append(next_notification_policy.notify_by)
        next_notification_policy = next_notification_policy.next()
    collected_steps = ", ".join(
        UserNotificationPolicy.NotificationChannel(step_id).label for step_id in collected_steps_ids
    )
    reason = ("Reason: " + reason + "\n") if reason is not None else ""
    reason += ("Further notification plan: " + collected_steps) if len(collected_steps_ids) > 0 else ""
    return reason


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_user_task(
    user_pk,
    alert_group_pk,
    previous_notification_policy_pk=None,
    reason=None,
    prevent_posting_to_thread=False,
    notify_even_acknowledged=False,
    important=False,
    notify_anyway=False,
):
    from apps.alerts.models import AlertGroup, UserHasNotification, UserNotificationBundle
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.user_management.models import User

    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        return f"notify_user_task: alert_group {alert_group_pk} doesn't exist"

    countdown = 0
    stop_escalation = False
    log_record = None
    is_notification_bundled = False
    user_notification_bundle = None

    with transaction.atomic():
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return f"notify_user_task: user {user_pk} doesn't exist"

        organization = alert_group.channel.organization

        if not user.is_notification_allowed:
            task_logger.info(f"notify_user_task: user {user.pk} notification is not allowed")
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                reason="notification is not allowed for user",
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN,
            ).save()
            return

        user_has_notification, _ = UserHasNotification.objects.get_or_create(
            user=user,
            alert_group=alert_group,
        )

        user_has_notification = UserHasNotification.objects.filter(pk=user_has_notification.pk).select_for_update()[0]

        if previous_notification_policy_pk is None:
            notification_policy = user.get_or_create_notification_policies(important=important).first()
            if notification_policy is None:
                task_logger.info(
                    f"notify_user_task: Failed to notify. No notification policies. user_id={user_pk} alert_group_id={alert_group_pk} important={important}"
                )
                return
            reason = build_user_notification_plan(notification_policy, reason)
        else:
            if notify_user_task.request.id != user_has_notification.active_notification_policy_id:
                task_logger.info(
                    f"notify_user_task: active_notification_policy_id mismatch. "
                    f"Duplication or non-active escalation triggered. "
                    f"Active: {user_has_notification.active_notification_policy_id}"
                )
                return

            try:
                notification_policy = UserNotificationPolicy.objects.get(pk=previous_notification_policy_pk)
                if notification_policy.user.organization != organization:
                    notification_policy = UserNotificationPolicy.objects.get(
                        order=notification_policy.order, user=user, important=important
                    )
                notification_policy = notification_policy.next()
            except UserNotificationPolicy.DoesNotExist:
                task_logger.info(
                    f"notify_user_taskLNotification policy {previous_notification_policy_pk} has been deleted"
                )
                return
            reason = None
        if notification_policy is None:
            stop_escalation = True
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FINISHED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                slack_prevent_posting=prevent_posting_to_thread,
            )
            task_logger.info(f"Personal escalation exceeded. User: {user.pk}, alert_group: {alert_group.pk}")
        else:
            if (
                (alert_group.acknowledged and not notify_even_acknowledged)
                or alert_group.resolved
                or alert_group.wiped_at
                or alert_group.root_alert_group
            ):
                return "Acknowledged, resolved, attached or wiped."

            if alert_group.silenced and not notify_anyway:
                task_logger.info(
                    f"notify_user_task: skip notification user {user.pk} because alert_group {alert_group.pk} is silenced"
                )
                return

            if notification_policy.step == UserNotificationPolicy.Step.WAIT:
                countdown = (
                    notification_policy.wait_delay.total_seconds() if notification_policy.wait_delay is not None else 0
                )
                log_record = UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                    notification_policy=notification_policy,
                    alert_group=alert_group,
                    slack_prevent_posting=prevent_posting_to_thread,
                    notification_step=notification_policy.step,
                )
                task_logger.info(f"notify_user_task: Waiting {countdown} to notify user {user.pk}")
            elif notification_policy.step == UserNotificationPolicy.Step.NOTIFY:
                user_to_be_notified_in_slack = (
                    notification_policy.notify_by == UserNotificationPolicy.NotificationChannel.SLACK
                )
                if user_to_be_notified_in_slack and alert_group.notify_in_slack_enabled is False:
                    log_record = UserNotificationPolicyLogRecord(
                        author=user,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                        notification_policy=notification_policy,
                        alert_group=alert_group,
                        reason="Alert group slack notifications are disabled",
                        slack_prevent_posting=prevent_posting_to_thread,
                        notification_step=notification_policy.step,
                        notification_channel=notification_policy.notify_by,
                        notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
                    )
                else:
                    # todo: feature flag
                    user_notification_bundle, _ = UserNotificationBundle.objects.get_or_create(
                        user=user, important=important, notification_channel=notification_policy.notify_by
                    )
                    user_notification_bundle = UserNotificationBundle.objects.filter(
                        pk=user_notification_bundle.pk
                    ).select_for_update()[0]
                    # check if notification needs to be bundled
                    if (
                        notification_policy.notify_by in UserNotificationBundle.NOTIFICATION_CHANNELS_TO_BUNDLE
                        and user_notification_bundle.notified_recently()
                    ):
                        user_notification_bundle.attach_notification(alert_group, notification_policy)
                        # schedule notification task for bundled notifications if it hasn't been scheduled or
                        # task eta is outdated
                        eta_is_valid = user_notification_bundle.eta_is_valid()
                        if not user_notification_bundle.notification_task_id or not eta_is_valid:
                            if not eta_is_valid:
                                task_logger.warning(
                                    f"ETA ({user_notification_bundle.eta}) is not valid for "
                                    f"user_notification_bundle {user_notification_bundle.id}, "
                                    f"task_id {user_notification_bundle.notification_task_id}. "
                                    f"Rescheduling the task"
                                )
                            new_eta = user_notification_bundle.get_notification_eta()
                            task_id = celery_uuid()
                            user_notification_bundle.notification_task_id = task_id
                            user_notification_bundle.eta = new_eta
                            user_notification_bundle.save(update_fields=["notification_task_id", "eta"])

                            transaction.on_commit(
                                partial(
                                    create_send_bundled_notification_task,
                                    user_notification_bundle,
                                    alert_group,
                                    task_id,
                                    new_eta,
                                )
                            )
                        is_notification_bundled = True

                    if not is_notification_bundled:
                        log_record = UserNotificationPolicyLogRecord(
                            author=user,
                            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                            notification_policy=notification_policy,
                            alert_group=alert_group,
                            reason=reason,
                            slack_prevent_posting=prevent_posting_to_thread,
                            notification_step=notification_policy.step,
                            notification_channel=notification_policy.notify_by,
                        )

        is_notification_triggered = (
            log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED
            if log_record
            else is_notification_bundled
        )
        # if this is the first notification step, and user hasn't been notified for this alert group - update metric
        if (
            is_notification_triggered
            and previous_notification_policy_pk is None
            and not user.personal_log_records.filter(
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                alert_group_id=alert_group_pk,
            ).exists()
        ):
            update_metrics_for_user.apply_async((user.id,))

        if log_record:  # log_record is None if user notification policy step is unspecified
            log_record.save()

        if not stop_escalation:
            # if the step is NOTIFY and notification was not not bundled, perform regular notification
            # and update time when user was notified
            if notification_policy.step == UserNotificationPolicy.Step.NOTIFY and not is_notification_bundled:
                transaction.on_commit(partial(create_perform_notification_task, log_record.pk, alert_group_pk))

                if user_notification_bundle:
                    user_notification_bundle.last_notified = timezone.now()
                    user_notification_bundle.save(update_fields=["last_notified"])

            task_id = celery_uuid()
            user_has_notification.update_active_task_id(task_id=task_id)

            transaction.on_commit(
                partial(
                    notify_user_task.apply_async,
                    (user.pk, alert_group.pk, notification_policy.pk, reason),
                    {
                        "notify_even_acknowledged": notify_even_acknowledged,
                        "notify_anyway": notify_anyway,
                        "prevent_posting_to_thread": prevent_posting_to_thread,
                    },
                    countdown=countdown + NEXT_ESCALATION_DELAY,
                    task_id=task_id,
                )
            )

        else:
            user_has_notification.update_active_task_id(task_id=None)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    dont_autoretry_for=(Retry,),
    max_retries=1 if settings.DEBUG else None,
)
def perform_notification(log_record_pk):
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.telegram.models import TelegramToUserConnector

    task_logger.info(f"perform_notification: log_record {log_record_pk}")

    try:
        log_record = UserNotificationPolicyLogRecord.objects.get(pk=log_record_pk)
    except UserNotificationPolicyLogRecord.DoesNotExist:
        task_logger.warning(
            f"perform_notification: log_record {log_record_pk} doesn't exist. Skipping remainder of task. "
            "The alert group associated with this log record may have been deleted."
        )
        return

    task_logger.info(f"perform_notification: found record for {log_record_pk}")

    user = log_record.author
    alert_group = log_record.alert_group
    notification_policy = log_record.notification_policy
    notification_channel = notification_policy.notify_by if notification_policy else None
    if user is None or notification_policy is None:
        UserNotificationPolicyLogRecord(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            reason="Expected data is missing",
            alert_group=alert_group,
            notification_step=notification_policy.step if notification_policy else None,
            notification_channel=notification_channel,
            notification_error_code=None,
        ).save()
        return

    if not user.is_notification_allowed:
        UserNotificationPolicyLogRecord(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            reason="notification is not allowed for user",
            alert_group=alert_group,
            notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN,
        ).save()
        return

    if notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
        phone_backend = PhoneBackend()
        phone_backend.notify_by_sms(user, alert_group, notification_policy)

    elif notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
        phone_backend = PhoneBackend()
        phone_backend.notify_by_call(user, alert_group, notification_policy)

    elif notification_channel == UserNotificationPolicy.NotificationChannel.TELEGRAM:
        try:
            TelegramToUserConnector.notify_user(user, alert_group, notification_policy)
        except RetryAfter as e:
            countdown = getattr(e, "retry_after", 3)
            raise perform_notification.retry((log_record_pk,), countdown=countdown, exc=e)

    elif notification_channel == UserNotificationPolicy.NotificationChannel.SLACK:
        # TODO: refactor checking the possibility of sending a notification in slack
        # Code below is not consistent.
        # We check various slack reasons to skip escalation in this task, in send_slack_notification,
        # before and after posting of slack message.
        if alert_group.skip_escalation_in_slack:
            notification_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK
            if alert_group.reason_to_skip_escalation == alert_group.RATE_LIMITED:
                notification_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_RATELIMIT
            elif alert_group.reason_to_skip_escalation == alert_group.CHANNEL_ARCHIVED:
                notification_error_code = (
                    UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_CHANNEL_IS_ARCHIVED
                )
            elif alert_group.reason_to_skip_escalation == alert_group.ACCOUNT_INACTIVE:
                notification_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR
            task_logger.debug(
                f"send_slack_notification for alert_group {alert_group.pk} failed because escalation in slack is "
                f"skipped, reason: '{alert_group.get_reason_to_skip_escalation_display()}'"
            )
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                reason=f"Skipped escalation in Slack, reason: '{alert_group.get_reason_to_skip_escalation_display()}'",
                alert_group=alert_group,
                notification_step=notification_policy.step,
                notification_channel=notification_channel,
                notification_error_code=notification_error_code,
            ).save()
            return

        if alert_group.notify_in_slack_enabled is True:
            # we cannot notify users in Slack if their team does not have Slack integration
            if alert_group.channel.organization.slack_team_identity is None:
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack team identity "
                    f"does not exist."
                )
                UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    reason="Slack team identity does not exist",
                    alert_group=alert_group,
                    notification_step=notification_policy.step,
                    notification_channel=notification_channel,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR,
                ).save()
                return

            if log_record.slack_prevent_posting:
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack posting is disabled."
                )
                UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    reason="Prevented from posting in Slack",
                    alert_group=alert_group,
                    notification_step=notification_policy.step,
                    notification_channel=notification_channel,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
                ).save()
                return

            retry_timeout_hours = 1
            if alert_group.slack_message:
                alert_group.slack_message.send_slack_notification(user, alert_group, notification_policy)
                task_logger.debug(f"Finished send_slack_notification for alert_group {alert_group.pk}.")
            # check how much time has passed since log record was created
            # to prevent eternal loop of restarting perform_notification task
            elif timezone.now() < log_record.created_at + timezone.timedelta(hours=retry_timeout_hours):
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack message "
                    f"does not exist. Restarting perform_notification."
                )
                restart_delay_seconds = 60
                perform_notification.apply_async((log_record_pk,), countdown=restart_delay_seconds)
            else:
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack message "
                    f"after {retry_timeout_hours} hours still does not exist"
                )
                UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    reason="Slack message does not exist",
                    alert_group=alert_group,
                    notification_step=notification_policy.step,
                    notification_channel=notification_channel,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK,
                ).save()
    else:
        try:
            backend_id = UserNotificationPolicy.NotificationChannel(notification_policy.notify_by).name
            backend = get_messaging_backend_from_id(backend_id)
        except ValueError:
            backend = None

        if backend is None:
            task_logger.debug("notify_user failed because messaging backend is not available")
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                reason="Messaging backend not available",
                alert_group=alert_group,
                notification_step=notification_policy.step,
                notification_channel=notification_channel,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR,
            ).save()
            return
        backend.notify_user(user, alert_group, notification_policy)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_bundled_notification(user_notification_bundle_id):
    from apps.alerts.models import AlertGroup, UserNotificationBundle
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    task_logger.info(f"Start send_bundled_notification for user_notification_bundle {user_notification_bundle_id}")
    with transaction.atomic():
        user_notification_bundle = UserNotificationBundle.objects.filter(
            pk=user_notification_bundle_id
        ).select_for_update()[0]

        if send_bundled_notification.request.id != user_notification_bundle.notification_task_id:
            task_logger.info(
                f"send_bundled_notification: notification_task_id mismatch. "
                f"Duplication or non-active notification triggered. "
                f"Active: {user_notification_bundle.notification_task_id}"
            )
            return

        notifications = user_notification_bundle.notifications.filter(bundle_uuid__isnull=True)

        alert_group_ids = [i.alert_group_id for i in notifications]
        # get active alert groups to notify about
        active_alert_groups = set(
            AlertGroup.objects.filter(
                id__in=alert_group_ids,
                resolved=False,
                acknowledged=False,
                silenced=False,
            ).values_list("id", flat=True)
        )
        created_lod_records = []
        skip_notification_ids = []
        perform_notifications = []

        for notification in notifications:
            if notification.alert_group_id not in active_alert_groups:
                task_logger.info(
                    f"alert_group {notification.alert_group_id} is not active or doesn't exist, skip notification"
                )
                skip_notification_ids.append(notification.id)
                continue

            # collect notifications for active alert groups
            perform_notifications.append(notification)

            log_record = UserNotificationPolicyLogRecord(
                author=user_notification_bundle.user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                notification_policy=notification.notification_policy,
                alert_group=notification.alert_group,
                notification_step=UserNotificationPolicy.Step.NOTIFY,
                notification_channel=user_notification_bundle.notification_channel,
            )
            log_record.save()
            created_lod_records.append(log_record)

        user_notification_bundle.notification_task_id = None
        user_notification_bundle.last_notified = timezone.now()
        user_notification_bundle.eta = None
        user_notification_bundle.save(update_fields=["notification_task_id", "last_notified", "eta"])

        if not user_notification_bundle.user.is_notification_allowed:
            for notification in perform_notifications:
                UserNotificationPolicyLogRecord(
                    author=user_notification_bundle.user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    reason="notification is not allowed for user",
                    alert_group=notification.alert_group,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN,
                ).save()
            notifications.delete()
            return

        if not perform_notifications:
            task_logger.info("no alert groups to notify about, skip notification")
            notifications.delete()

        elif len(perform_notifications) == 1:
            # perform regular notification
            log_record = created_lod_records[0]
            task_logger.info(
                f"there is only one alert group in bundled notification, perform regular notification. "
                f"alert_group {log_record.alert_group_id}"
            )
            transaction.on_commit(partial(create_perform_notification_task, log_record.pk, log_record.alert_group_id))
            notifications.delete()
        else:
            notifications.filter(id__in=skip_notification_ids).delete()
            bundle_uuid = uuid4()
            notifications.update(bundle_uuid=bundle_uuid)
            task_logger.info(
                f"perform notification for alert groups with ids: {active_alert_groups}, bundle_uuid: {bundle_uuid}"
            )

            if user_notification_bundle.notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                # todo:
                #  notify_by_sms_bundle:
                #  - call send sms async
                #  - filter notifications by bundle_uuid
                #  - delete notifications
                # phone_backend = PhoneBackend()
                # phone_backend.notify_by_sms_bundle(user_notification_bundle.user_id, bundle_uuid)
                pass

        task_logger.info(
            f"Finished send_bundled_notification for user_notification_bundle {user_notification_bundle_id}"
        )


# deprecated
@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def send_user_notification_signal(log_record_pk):
    # Triggers user_notification_action_triggered_signal
    # This signal is only connected to UserSlackRepresentative and triggers posting message to Slack about some
    # FAILED notifications (see NotificationDeliveryStep and ERRORS_TO_SEND_IN_SLACK_CHANNEL).
    # No need to call it here.
    pass
