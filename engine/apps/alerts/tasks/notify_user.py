import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from kombu.utils.uuid import uuid as celery_uuid

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.messaging import get_messaging_backend_from_id
from apps.metrics_exporter.helpers import metrics_update_user_cache
from apps.phone_notifications.phone_backend import PhoneBackend
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


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
    from apps.alerts.models import AlertGroup, UserHasNotification
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.user_management.models import User

    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        return f"notify_user_task: alert_group {alert_group_pk} doesn't exist"

    countdown = 0
    stop_escalation = False
    log_message = ""
    log_record = None

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
            notification_policy = UserNotificationPolicy.objects.filter(user=user, important=important).first()
            if notification_policy is None:
                task_logger.info(
                    f"notify_user_task: Failed to notify. No notification policies. user_id={user_pk} alert_group_id={alert_group_pk} important={important}"
                )
                return
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
            log_message += "Personal escalation exceeded"
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
                if notification_policy.wait_delay is not None:
                    delay_in_seconds = notification_policy.wait_delay.total_seconds()
                else:
                    delay_in_seconds = 0
                countdown = delay_in_seconds
                log_record = UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                    notification_policy=notification_policy,
                    alert_group=alert_group,
                    slack_prevent_posting=prevent_posting_to_thread,
                    notification_step=notification_policy.step,
                )
                task_logger.info(f"notify_user_task: Waiting {delay_in_seconds} to notify user {user.pk}")
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
                        reason=reason,
                        slack_prevent_posting=prevent_posting_to_thread,
                        notification_step=notification_policy.step,
                        notification_channel=notification_policy.notify_by,
                        notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
                    )
                else:
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
        if log_record:  # log_record is None if user notification policy step is unspecified
            # if this is the first notification step, and user hasn't been notified for this alert group - update metric
            if (
                log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED
                and previous_notification_policy_pk is None
                and not user.personal_log_records.filter(
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                    alert_group_id=alert_group_pk,
                ).exists()
            ):
                metrics_update_user_cache(user)

            log_record.save()
            if notify_user_task.request.retries == 0:
                transaction.on_commit(lambda: send_user_notification_signal.apply_async((log_record.pk,)))

        if not stop_escalation:
            if notification_policy.step != UserNotificationPolicy.Step.WAIT:
                transaction.on_commit(lambda: perform_notification.apply_async((log_record.pk,)))

            delay = NEXT_ESCALATION_DELAY
            if countdown is not None:
                delay += countdown
            task_id = celery_uuid()

            user_has_notification.active_notification_policy_id = task_id
            user_has_notification.save(update_fields=["active_notification_policy_id"])

            transaction.on_commit(
                lambda: notify_user_task.apply_async(
                    (user.pk, alert_group.pk, notification_policy.pk, reason),
                    {
                        "notify_even_acknowledged": notify_even_acknowledged,
                        "notify_anyway": notify_anyway,
                        "prevent_posting_to_thread": prevent_posting_to_thread,
                    },
                    countdown=delay,
                    task_id=task_id,
                )
            )

        else:
            user_has_notification.active_notification_policy_id = None
            user_has_notification.save(update_fields=["active_notification_policy_id"])


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def perform_notification(log_record_pk):
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.telegram.models import TelegramToUserConnector

    log_record = UserNotificationPolicyLogRecord.objects.get(pk=log_record_pk)

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
        TelegramToUserConnector.notify_user(user, alert_group, notification_policy)

    elif notification_channel == UserNotificationPolicy.NotificationChannel.SLACK:
        # TODO: refactor checking the possibility of sending a notification in slack
        # Code below is not consistent.
        # We check various slack reasons to skip escalation in this task, in send_slack_notification,
        # before and after posting of slack message.
        if alert_group.reason_to_skip_escalation == alert_group.RATE_LIMITED:
            task_logger.debug(
                f"send_slack_notification for alert_group {alert_group.pk} failed because of slack ratelimit."
            )
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                reason="Slack ratelimit",
                alert_group=alert_group,
                notification_step=notification_policy.step,
                notification_channel=notification_channel,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_RATELIMIT,
            ).save()
            return

        if alert_group.notify_in_slack_enabled is True and not log_record.slack_prevent_posting:
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

            retry_timeout_hours = 1
            slack_message = alert_group.get_slack_message()
            if slack_message is not None:
                slack_message.send_slack_notification(user, alert_group, notification_policy)
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
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def send_user_notification_signal(log_record_pk):
    start_time = time.time()

    from apps.base.models import UserNotificationPolicyLogRecord

    task_logger.debug(f"LOG RECORD PK: {log_record_pk}")
    task_logger.debug(f"LOG RECORD LAST: {UserNotificationPolicyLogRecord.objects.last()}")

    log_record = UserNotificationPolicyLogRecord.objects.get(pk=log_record_pk)
    user_notification_action_triggered_signal.send(sender=send_user_notification_signal, log_record=log_record)

    task_logger.debug("--- USER SIGNAL TOOK %s seconds ---" % (time.time() - start_time))
