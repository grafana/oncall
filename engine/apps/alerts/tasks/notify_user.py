import typing
from functools import partial
from uuid import uuid4

from celery.exceptions import Retry
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from kombu.utils.uuid import uuid as celery_uuid
from telegram.error import RetryAfter

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.alerts.tasks.send_update_log_report_signal import send_update_log_report_signal
from apps.base.messaging import get_messaging_backend_from_id
from apps.metrics_exporter.tasks import update_metrics_for_user
from apps.phone_notifications.phone_backend import PhoneBackend
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, UserNotificationBundle
    from apps.base.models import UserNotificationPolicy
    from apps.user_management.models import User


RETRY_TIMEOUT_HOURS = 1


def schedule_send_bundled_notification_task(
    user_notification_bundle: "UserNotificationBundle", alert_group: "AlertGroup"
):
    """Schedule a task to send bundled notifications"""
    send_bundled_notification.apply_async(
        (user_notification_bundle.id,),
        eta=user_notification_bundle.eta,
        task_id=user_notification_bundle.notification_task_id,
    )
    task_logger.info(
        f"Scheduled send_bundled_notification task {user_notification_bundle.notification_task_id}, "
        f"user_notification_bundle: {user_notification_bundle.id}, alert_group {alert_group.id}, "
        f"eta: {user_notification_bundle.eta}"
    )


def schedule_perform_notification_task(
    log_record_pk: int, alert_group_pk: int, use_default_notification_policy_fallback: bool
):
    task = perform_notification.apply_async((log_record_pk, use_default_notification_policy_fallback))
    task_logger.info(
        f"Created perform_notification task {task} log_record={log_record_pk} " f"alert_group={alert_group_pk}"
    )


def build_notification_reason_for_log_record(
    notification_policies: typing.List["UserNotificationPolicy"], reason: typing.Optional[str]
) -> str:
    from apps.base.models import UserNotificationPolicy

    # Here we collect a brief overview of notification steps configured for user to send it to thread.
    collected_steps_ids = []
    for next_notification_policy in notification_policies:
        if next_notification_policy.step == UserNotificationPolicy.Step.NOTIFY:
            if next_notification_policy.notify_by not in collected_steps_ids:
                collected_steps_ids.append(next_notification_policy.notify_by)

    collected_steps = ", ".join(
        UserNotificationPolicy.NotificationChannel(step_id).label for step_id in collected_steps_ids
    )
    reason = ("Reason: " + reason + "\n") if reason is not None else ""
    reason += ("Further notification plan: " + collected_steps) if len(collected_steps_ids) > 0 else ""
    return reason


def update_metric_if_needed(user: "User", active_alert_group_ids: typing.List[int]):
    from apps.base.models import UserNotificationPolicyLogRecord

    # get count of alert groups with only one personal log record with type "triggered"
    alert_groups_with_one_log = (
        user.personal_log_records.filter(
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
            alert_group_id__in=active_alert_group_ids,
        )
        .values("alert_group")
        .annotate(count=Count("alert_group"))
        .filter(count=1)
        .count()
    )

    if alert_groups_with_one_log > 0:
        update_metrics_for_user.apply_async((user.id, alert_groups_with_one_log))


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
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord, UserHasNotification, UserNotificationBundle
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
        using_fallback_default_notification_policy_step = False

        if previous_notification_policy_pk is None:
            (
                using_fallback_default_notification_policy_step,
                notification_policies,
            ) = user.get_notification_policies_or_use_default_fallback(important=important)
            if not notification_policies:
                task_logger.info(
                    f"notify_user_task: Failed to notify. No notification policies. user_id={user_pk} alert_group_id={alert_group_pk} important={important}"
                )
                return
            reason = build_notification_reason_for_log_record(notification_policies, reason)
            notification_policy = notification_policies[0]
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
                if notification_policy.user != user:
                    notification_policy = UserNotificationPolicy.objects.get(
                        order=notification_policy.order, user=user, important=important
                    )
                notification_policy = notification_policy.next()
            except UserNotificationPolicy.DoesNotExist:
                task_logger.info(
                    f"notify_user_task: Notification policy {previous_notification_policy_pk} has been deleted"
                )
                return
            reason = None

        def _create_user_notification_policy_log_record(**kwargs):
            return UserNotificationPolicyLogRecord(
                **kwargs,
                using_fallback_default_notification_policy_step=using_fallback_default_notification_policy_step,
            )

        def _create_notification_finished_user_notification_policy_log_record():
            return _create_user_notification_policy_log_record(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FINISHED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                slack_prevent_posting=prevent_posting_to_thread,
            )

        if notification_policy is None:
            stop_escalation = True
            log_record = _create_notification_finished_user_notification_policy_log_record()
            task_logger.info(f"Personal escalation exceeded. User: {user.pk}, alert_group: {alert_group.pk}")
        else:
            if (
                # don't force notify direct paged user who has already acknowledged the alert group
                # after the last time they were paged.
                notify_even_acknowledged
                and (
                    direct_paging_log_record := alert_group.log_records.filter(
                        type=AlertGroupLogRecord.TYPE_DIRECT_PAGING, step_specific_info__user=user.public_primary_key
                    ).last()
                )
                and alert_group.log_records.filter(
                    type=AlertGroupLogRecord.TYPE_ACK, author=user, created_at__gte=direct_paging_log_record.created_at
                ).exists()
            ):
                notify_even_acknowledged = False
                task_logger.info(f"notify_even_acknowledged=False for user {user.pk}, alert_group {alert_group.pk})")

            if (
                (alert_group.acknowledged and not notify_even_acknowledged)
                or (alert_group.silenced and not notify_anyway)
                or alert_group.resolved
                or alert_group.wiped_at
                or alert_group.root_alert_group
            ):
                task_logger.info(
                    f"notify_user_task: skip notification user {user.pk}, alert_group {alert_group.pk} is "
                    f"{alert_group.state} and/or attached or wiped"
                )
                return "Acknowledged, resolved, silenced, attached or wiped."

            if notification_policy.step == UserNotificationPolicy.Step.WAIT:
                countdown = (
                    notification_policy.wait_delay.total_seconds() if notification_policy.wait_delay is not None else 0
                )
                log_record = _create_user_notification_policy_log_record(
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
                    log_record = _create_user_notification_policy_log_record(
                        author=user,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                        notification_policy=notification_policy,
                        alert_group=alert_group,
                        reason="Alert group Slack notifications are disabled",
                        slack_prevent_posting=prevent_posting_to_thread,
                        notification_step=notification_policy.step,
                        notification_channel=notification_policy.notify_by,
                        notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
                    )
                else:
                    if (
                        settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED
                        and UserNotificationBundle.notification_is_bundleable(notification_policy.notify_by)
                    ):
                        user_notification_bundle, _ = UserNotificationBundle.objects.select_for_update().get_or_create(
                            user=user, important=important, notification_channel=notification_policy.notify_by
                        )
                        # check if notification needs to be bundled
                        if user_notification_bundle.notified_recently():
                            user_notification_bundle.append_notification(alert_group, notification_policy)
                            # schedule send_bundled_notification task if it hasn't been scheduled or the task eta is
                            # outdated
                            eta_is_valid = user_notification_bundle.eta_is_valid()
                            if not eta_is_valid:
                                task_logger.warning(
                                    f"ETA is not valid - {user_notification_bundle.eta}, "
                                    f"user_notification_bundle {user_notification_bundle.id}, "
                                    f"task_id {user_notification_bundle.notification_task_id}. "
                                    f"Rescheduling the send_bundled_notification task"
                                )
                            if not user_notification_bundle.notification_task_id or not eta_is_valid:
                                user_notification_bundle.notification_task_id = celery_uuid()
                                user_notification_bundle.eta = user_notification_bundle.get_notification_eta()
                                user_notification_bundle.save(update_fields=["notification_task_id", "eta"])

                                transaction.on_commit(
                                    partial(
                                        schedule_send_bundled_notification_task, user_notification_bundle, alert_group
                                    )
                                )
                            is_notification_bundled = True

                    if not is_notification_bundled:
                        log_record = _create_user_notification_policy_log_record(
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
                update_metrics_for_user.apply_async((user.id,))
            log_record.save()

        if using_fallback_default_notification_policy_step:
            # if we are using default notification policy, we're done escalating.. there's no further notification
            # policy steps in this case. Kick off the perform_notification task, create the
            # TYPE_PERSONAL_NOTIFICATION_FINISHED log record, and reset the active_notification_policy_id
            transaction.on_commit(
                partial(
                    schedule_perform_notification_task,
                    log_record.pk,
                    alert_group_pk,
                    using_fallback_default_notification_policy_step,
                )
            )
            _create_notification_finished_user_notification_policy_log_record()
            user_has_notification.update_active_task_id(None)
        elif not stop_escalation:
            # if the step is NOTIFY and notification was not not bundled, perform regular notification
            # and update time when user was notified
            if notification_policy.step != UserNotificationPolicy.Step.WAIT and not is_notification_bundled:
                transaction.on_commit(
                    partial(
                        schedule_perform_notification_task,
                        log_record.pk,
                        alert_group_pk,
                        using_fallback_default_notification_policy_step,
                    )
                )

                if user_notification_bundle:
                    user_notification_bundle.last_notified_at = timezone.now()
                    user_notification_bundle.save(update_fields=["last_notified_at"])

            task_id = celery_uuid()
            user_has_notification.update_active_task_id(task_id)

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
            user_has_notification.update_active_task_id(None)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    dont_autoretry_for=(Retry,),
    max_retries=1 if settings.DEBUG else None,
)
def perform_notification(log_record_pk, use_default_notification_policy_fallback):
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
    notification_policy = (
        UserNotificationPolicy.get_default_fallback_policy(user)
        if use_default_notification_policy_fallback
        else log_record.notification_policy
    )
    notification_channel = notification_policy.notify_by if notification_policy else None

    if user is None or notification_policy is None:
        UserNotificationPolicyLogRecord(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy if not use_default_notification_policy_fallback else None,
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

    if alert_group.resolved:
        # skip notification if alert group was resolved
        UserNotificationPolicyLogRecord(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy if not use_default_notification_policy_fallback else None,
            reason="Skipped notification because alert group is resolved",
            alert_group=alert_group,
            notification_step=notification_policy.step if notification_policy else None,
            notification_channel=notification_channel,
            notification_error_code=None,
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
            task_logger.exception(f"Telegram API rate limit exceeded. Retry after {e.retry_after} seconds.")
            # check how much time has passed since log record was created
            # to prevent eternal loop of restarting perform_notification task
            if timezone.now() < log_record.created_at + timezone.timedelta(hours=RETRY_TIMEOUT_HOURS):
                countdown = getattr(e, "retry_after", 3)
                perform_notification.apply_async(
                    (log_record_pk, use_default_notification_policy_fallback), countdown=countdown
                )
            else:
                task_logger.debug(
                    f"telegram notification for alert_group {alert_group.pk} failed because of rate limit"
                )
                UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    reason="Telegram rate limit exceeded",
                    alert_group=alert_group,
                    notification_step=notification_policy.step,
                    notification_channel=notification_channel,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_TELEGRAM_RATELIMIT,
                ).save()
            return

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
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
                    notification_policy=notification_policy,
                    reason="Prevented from posting in Slack",
                    alert_group=alert_group,
                    notification_step=notification_policy.step,
                    notification_channel=notification_channel,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
                ).save()
                return

            if alert_group.slack_message:
                alert_group.slack_message.send_slack_notification(user, alert_group, notification_policy)
                task_logger.debug(f"Finished send_slack_notification for alert_group {alert_group.pk}.")

            # check how much time has passed since log record was created
            # to prevent eternal loop of restarting perform_notification task
            elif timezone.now() < log_record.created_at + timezone.timedelta(hours=RETRY_TIMEOUT_HOURS):
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack message "
                    f"does not exist. Restarting perform_notification."
                )
                restart_delay_seconds = 60
                perform_notification.apply_async(
                    (log_record_pk, use_default_notification_policy_fallback), countdown=restart_delay_seconds
                )
            else:
                task_logger.debug(
                    f"send_slack_notification for alert_group {alert_group.pk} failed because slack message "
                    f"after {RETRY_TIMEOUT_HOURS} hours still does not exist"
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
def send_bundled_notification(user_notification_bundle_id: int):
    """
    The task filters bundled notifications, attached to the current user_notification_bundle, by active alert groups,
    creates notification log records and updates user_notification_bundle.
    If there are no active alert groups - nothing else happens. If there is only one active alert group - regular
    notification will be performed (called perform_notification task). Otherwise - "send bundled notification" method of
    the current notification channel will be called.
    """
    from apps.alerts.models import AlertGroup, UserNotificationBundle
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    task_logger.info(f"Start send_bundled_notification for user_notification_bundle {user_notification_bundle_id}")
    with transaction.atomic():
        try:
            user_notification_bundle = UserNotificationBundle.objects.filter(
                pk=user_notification_bundle_id
            ).select_for_update()[0]
        except IndexError:
            task_logger.info(
                f"user_notification_bundle {user_notification_bundle_id} doesn't exist. "
                f"The user associated with this notification bundle may have been deleted."
            )
            return

        if send_bundled_notification.request.id != user_notification_bundle.notification_task_id:
            task_logger.info(
                f"send_bundled_notification: notification_task_id mismatch. "
                f"Duplication or non-active notification triggered. "
                f"Active: {user_notification_bundle.notification_task_id}"
            )
            return

        notifications = user_notification_bundle.notifications.filter(bundle_uuid__isnull=True).select_related(
            "alert_group"
        )

        log_records_to_create: typing.List["UserNotificationPolicyLogRecord"] = []
        skip_notification_ids: typing.List[int] = []
        active_alert_group_ids: typing.Set[int] = set()
        log_record_notification_triggered = None
        is_notification_allowed = user_notification_bundle.user.is_notification_allowed
        bundle_uuid = uuid4()

        # create logs
        for notification in notifications:
            if notification.alert_group.status != AlertGroup.NEW:
                task_logger.info(f"alert_group {notification.alert_group_id} is not active, skip notification")
                skip_notification_ids.append(notification.id)
                continue
            elif not is_notification_allowed:
                log_record_notification_failed = UserNotificationPolicyLogRecord(
                    author=user_notification_bundle.user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    reason="notification is not allowed for user",
                    alert_group=notification.alert_group,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN,
                )
                log_records_to_create.append(log_record_notification_failed)
                active_alert_group_ids.add(notification.alert_group_id)
                continue

            # collect notifications for active alert groups
            active_alert_group_ids.add(notification.alert_group_id)

            log_record_notification_triggered = UserNotificationPolicyLogRecord(
                author=user_notification_bundle.user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                alert_group=notification.alert_group,
                notification_policy=notification.notification_policy,
                notification_step=UserNotificationPolicy.Step.NOTIFY,
                notification_channel=user_notification_bundle.notification_channel,
            )
            log_records_to_create.append(log_record_notification_triggered)

        # delete non-active notifications and update bundle_uuid for the rest notifications
        if not is_notification_allowed:
            notifications.delete()
        else:
            notifications.filter(id__in=skip_notification_ids).delete()
            notifications.update(bundle_uuid=bundle_uuid)

        if len(log_records_to_create) == 1 and log_record_notification_triggered:
            # perform regular notification
            log_record_notification_triggered.save()
            task_logger.info(
                f"there is only one alert group in bundled notification, perform regular notification. "
                f"alert_group {log_record_notification_triggered.alert_group_id}"
            )
            transaction.on_commit(
                partial(
                    schedule_perform_notification_task,
                    log_record_notification_triggered.pk,
                    log_record_notification_triggered.alert_group_id,
                    False,
                )
            )
        else:
            UserNotificationPolicyLogRecord.objects.bulk_create(log_records_to_create, batch_size=5000)

            if not active_alert_group_ids or not is_notification_allowed:
                task_logger.info(
                    f"no alert groups to notify about or notification is not allowed for user "
                    f"{user_notification_bundle.user_id}"
                )
            else:
                task_logger.info(
                    f"perform bundled notification for alert groups with ids: {active_alert_group_ids}, "
                    f"bundle_uuid: {bundle_uuid}"
                )
                if user_notification_bundle.notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                    PhoneBackend.notify_by_sms_bundle_async(user_notification_bundle.user, bundle_uuid)

        user_notification_bundle.notification_task_id = None
        user_notification_bundle.last_notified_at = timezone.now()
        user_notification_bundle.eta = None
        user_notification_bundle.save(update_fields=["notification_task_id", "last_notified_at", "eta"])

    for alert_group_id in active_alert_group_ids:
        transaction.on_commit(partial(send_update_log_report_signal.apply_async, (None, alert_group_id)))

    # update metric
    transaction.on_commit(partial(update_metric_if_needed, user_notification_bundle.user, active_alert_group_ids))

    task_logger.info(f"Finished send_bundled_notification for user_notification_bundle {user_notification_bundle_id}")


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
