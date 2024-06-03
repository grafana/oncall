import datetime
import typing

import requests
from django.conf import settings
from django.db.models import Avg, F, Max, Q
from django.utils import timezone

from apps.alerts.tasks.task_logger import task_logger
from apps.phone_notifications.models import SMSRecord
from apps.twilioapp.models import TwilioSMSstatuses
from common.custom_celery_tasks.log_exception_on_failure_task import shared_log_exception_on_failure_task
from common.database import get_random_readonly_database_key_if_present_otherwise_default

if typing.TYPE_CHECKING:
    from apps.alerts.models.alert_group import AlertGroup


class AlertGroupEscalationPolicyExecutionAuditException(BaseException):
    """This exception is raised when an alert group's escalation policy did not execute execute properly for some reason"""


def send_alert_group_escalation_auditor_task_heartbeat() -> None:
    heartbeat_url = settings.ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL
    if heartbeat_url:
        task_logger.info(f"Sending heartbeat to configured URL: {heartbeat_url}")
        requests.get(heartbeat_url).raise_for_status()
        task_logger.info(f"Heartbeat successfully sent to {heartbeat_url}")
    else:
        task_logger.info("Skipping sending heartbeat as no heartbeat URL is configured")


def audit_alert_group_escalation(alert_group: "AlertGroup") -> None:
    raw_escalation_snapshot: dict = alert_group.raw_escalation_snapshot
    alert_group_id = alert_group.id
    base_msg = f"Alert group {alert_group_id}"

    if not raw_escalation_snapshot:
        msg = f"{base_msg} does not have an escalation snapshot associated with it, this should never occur"

        task_logger.warning(msg)
        raise AlertGroupEscalationPolicyExecutionAuditException(msg)

    if not raw_escalation_snapshot.get("escalation_chain_snapshot"):
        task_logger.info(
            f"{base_msg} does not have an escalation chain associated with it, and therefore it is expected "
            "that it will not have an escalation snapshot, skipping further validation"
        )
        return

    task_logger.info(f"{base_msg} has an escalation snapshot associated with it, auditing if it executed properly")

    escalation_policies_snapshots = raw_escalation_snapshot.get("escalation_policies_snapshots")

    if not escalation_policies_snapshots:
        task_logger.info(
            f"{base_msg}'s escalation snapshot has an empty escalation_policies_snapshots, skipping further validation"
        )
        return
    task_logger.info(
        f"{base_msg}'s escalation snapshot has a populated escalation_policies_snapshots, continuing validation"
    )

    if alert_group.next_step_eta_is_valid() is False:
        msg = f"{base_msg}'s escalation snapshot does not have a valid next_step_eta: {alert_group.next_step_eta}"

        task_logger.warning(msg)
        raise AlertGroupEscalationPolicyExecutionAuditException(msg)

    task_logger.info(f"{base_msg}'s escalation snapshot has a valid next_step_eta: {alert_group.next_step_eta}")

    num_of_executed_escalation_policy_snapshots = (
        alert_group.last_active_escalation_policy_order + 1
        if alert_group.last_active_escalation_policy_order is not None
        else 0
    )

    if num_of_executed_escalation_policy_snapshots == 0:
        task_logger.info(
            f"{base_msg}'s escalation snapshot does not have any executed escalation policies, skipping further validation"
        )
    else:
        task_logger.info(
            f"{base_msg}'s escalation snapshot has {num_of_executed_escalation_policy_snapshots} executed escalation policies"
        )

    check_alert_group_personal_notifications_task.apply_async((alert_group_id,))

    task_logger.info(f"{base_msg} passed the audit checks")


@shared_log_exception_on_failure_task
def check_alert_group_personal_notifications_task(alert_group_id) -> None:
    # Check personal notifications are completed
    # triggered (< 5min ago) == failed + success
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    triggered = UserNotificationPolicyLogRecord.objects.filter(
        alert_group_id=alert_group_id,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        notification_policy__isnull=False,  # filter out deleted policies
        created_at__lte=timezone.now() - timezone.timedelta(minutes=5),
    ).count()
    completed = UserNotificationPolicyLogRecord.objects.filter(
        Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED)
        | Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS),
        alert_group_id=alert_group_id,
        notification_policy__isnull=False,  # filter out deleted policies
        notification_step=UserNotificationPolicy.Step.NOTIFY,
    ).count()

    # sent SMS messages are considered completed for our purpose here
    # (ie. do not wait for Twilio delivered confirmation)
    sent_but_not_delivered_sms = SMSRecord.objects.filter(
        represents_alert_group_id=alert_group_id,
        twilioapp_twiliosmss__status__in=[TwilioSMSstatuses.SENT, TwilioSMSstatuses.ACCEPTED],
    ).count()

    base_msg = f"Alert group {alert_group_id}"
    completed += sent_but_not_delivered_sms
    delta = triggered - completed
    if delta > 0:
        task_logger.info(f"{base_msg} has ({delta}) uncompleted personal notifications")
    else:
        task_logger.info(f"{base_msg} personal notifications check passed")


@shared_log_exception_on_failure_task
def check_personal_notifications_task() -> None:
    """
    This task checks that triggered personal notifications are completed.
    It will log the triggered/completed values to be used as metrics.

    Attention: don't retry this task, the idea is to be alerted of failures
    """
    from apps.alerts.models import AlertGroup
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    # use readonly database if available
    readonly_db = get_random_readonly_database_key_if_present_otherwise_default()

    now = timezone.now()

    # consider alert groups from the last 2 days
    alert_groups = AlertGroup.objects.using(readonly_db).filter(
        started_at__range=(now - timezone.timedelta(days=2), now),
    )

    # review notifications triggered in the last 20-minute window
    # (task should run periodically about every 15 minutes)
    since = now - timezone.timedelta(minutes=20)

    log_records_qs = UserNotificationPolicyLogRecord.objects.using(readonly_db)
    # personal notifications triggered in the given window for those alert groups
    triggered = log_records_qs.filter(
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        created_at__gte=since,
        created_at__lte=now,
        alert_group__in=alert_groups,
    ).count()

    # personal notifications completed in the given window for those alert groups
    completed = log_records_qs.filter(
        Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED)
        | Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS),
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        created_at__gt=since,
        created_at__lte=now,
        alert_group__in=alert_groups,
    ).count()

    task_logger.info(f"personal_notifications_triggered={triggered} personal_notifications_completed={completed}")


@shared_log_exception_on_failure_task
def check_escalation_finished_task() -> None:
    """
    This task takes alert groups with active escalation, checks if escalation snapshot with escalation policies
    was created and next escalation step eta is higher than now minus 5 min for every active alert group,
    what means that escalations are going as expected.
    If there are alert groups that failed the check, it raises exception. Otherwise - send heartbeat. Missing heartbeat
    raises alert.

    Attention: don't retry this task, the idea is to be alerted of failures
    """
    from apps.alerts.models import AlertGroup

    now = timezone.now() - datetime.timedelta(minutes=5)
    two_days_ago = now - datetime.timedelta(days=2)

    # Total alert groups over last 2 days
    alert_groups = AlertGroup.objects.using(get_random_readonly_database_key_if_present_otherwise_default()).filter(
        started_at__range=(two_days_ago, now),
    )
    total_alert_groups_count = alert_groups.count()

    creation_deltas = alert_groups.aggregate(
        avg_delta=Avg(F("started_at") - F("received_at")),
        max_delta=Max(F("started_at") - F("received_at")),
    )
    avg_delta = creation_deltas["avg_delta"]
    max_delta = creation_deltas["max_delta"]
    if avg_delta:
        task_logger.info(f"Alert group ingestion/creation avg delta seconds: {avg_delta.total_seconds():.2f}")
        task_logger.info(f"Alert group ingestion/creation max delta seconds: {max_delta.total_seconds():.2f}")

    # Filter alert groups with active escalations (that could fail)
    alert_groups = alert_groups.filter_active()

    task_logger.info(
        f"There are {len(alert_groups)} alert group(s) to audit"
        if alert_groups.exists()
        else "There are no alert groups to audit, everything is good :)"
    )

    alert_group_ids_that_failed_audit: typing.List[str] = []

    for alert_group in alert_groups:
        try:
            audit_alert_group_escalation(alert_group)
        except AlertGroupEscalationPolicyExecutionAuditException:
            alert_group_ids_that_failed_audit.append(str(alert_group.id))

    failed_alert_groups_count = len(alert_group_ids_that_failed_audit)
    success_ratio = (
        100
        if total_alert_groups_count == 0
        else (total_alert_groups_count - failed_alert_groups_count) / total_alert_groups_count * 100
    )
    task_logger.info(f"Alert groups failing escalation: {failed_alert_groups_count}")
    task_logger.info(f"Alert groups succeeding escalation: {total_alert_groups_count - failed_alert_groups_count}")
    task_logger.info(f"Alert groups total escalations: {total_alert_groups_count}")
    task_logger.info(f"Alert group notifications success ratio: {success_ratio:.2f}")

    if alert_group_ids_that_failed_audit:
        msg = f"The following alert group id(s) failed auditing: {', '.join(alert_group_ids_that_failed_audit)}"

        task_logger.warning(msg)
        raise AlertGroupEscalationPolicyExecutionAuditException(msg)

    task_logger.info("There were no alert groups that failed auditing")
    send_alert_group_escalation_auditor_task_heartbeat()
