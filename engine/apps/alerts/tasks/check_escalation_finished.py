import datetime
import typing

import requests
from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.alerts.tasks.task_logger import task_logger
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
    escalation_snapshot = alert_group.escalation_snapshot
    alert_group_id = alert_group.id
    base_msg = f"Alert group {alert_group_id}"

    if not alert_group.escalation_chain_exists:
        task_logger.info(
            f"{base_msg} does not have an escalation chain associated with it, and therefore it is expected "
            "that it will not have an escalation snapshot, skipping further validation"
        )
        return

    if not escalation_snapshot:
        msg = f"{base_msg} does not have an escalation snapshot associated with it, this should never occur"

        task_logger.warning(msg)
        raise AlertGroupEscalationPolicyExecutionAuditException(msg)

    task_logger.info(f"{base_msg} has an escalation snapshot associated with it, auditing if it executed properly")

    escalation_policies_snapshots = escalation_snapshot.escalation_policies_snapshots

    if not escalation_policies_snapshots:
        task_logger.info(
            f"{base_msg}'s escalation snapshot has an empty escalation_policies_snapshots, skipping further validation"
        )
        return
    task_logger.info(
        f"{base_msg}'s escalation snapshot has a populated escalation_policies_snapshots, continuing validation"
    )

    if escalation_snapshot.next_step_eta_is_valid() is False:
        raise AlertGroupEscalationPolicyExecutionAuditException(
            f"{base_msg}'s escalation snapshot does not have a valid next_step_eta: {escalation_snapshot.next_step_eta}"
        )
    task_logger.info(f"{base_msg}'s escalation snapshot has a valid next_step_eta: {escalation_snapshot.next_step_eta}")

    executed_escalation_policy_snapshots = escalation_snapshot.executed_escalation_policy_snapshots
    num_of_executed_escalation_policy_snapshots = len(executed_escalation_policy_snapshots)

    if num_of_executed_escalation_policy_snapshots == 0:
        task_logger.info(
            f"{base_msg}'s escalation snapshot does not have any executed escalation policies, skipping further validation"
        )
    else:
        task_logger.info(
            f"{base_msg}'s escalation snapshot has {num_of_executed_escalation_policy_snapshots} executed escalation policies"
        )

    # TODO: consider adding the below checks later on. This is it a bit trickier to properly audit as the
    # number of log records can vary if there are any STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW or
    # STEP_REPEAT_ESCALATION_N_TIMES escalation policy steps in the escalation chain
    # see conversations in the original PR (https://github.com/grafana/oncall/pull/1266) for more context on this
    #
    # compare number of triggered/failed alert group log records to the number of executed
    # escalation policy snapshot steps
    # num_of_relevant_log_records = AlertGroupLogRecord.objects.filter(
    #     alert_group_id=alert_group_id,
    #     type__in=[AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED, AlertGroupLogRecord.TYPE_ESCALATION_FAILED],
    # ).count()

    # if num_of_relevant_log_records < num_of_executed_escalation_policy_snapshots:
    #     raise AlertGroupEscalationPolicyExecutionAuditException(
    #         f"{base_msg}'s number of triggered/failed alert group log records ({num_of_relevant_log_records}) is less "
    #         f"than the number of executed escalation policy snapshot steps ({num_of_executed_escalation_policy_snapshots})"
    #     )

    # task_logger.info(
    #     f"{base_msg}'s number of triggered/failed alert group log records ({num_of_relevant_log_records}) is greater "
    #     f"than or equal to the number of executed escalation policy snapshot steps ({num_of_executed_escalation_policy_snapshots})"
    # )

    task_logger.info(f"{base_msg} passed the audit checks")


@shared_task
def check_escalation_finished_task() -> None:
    """
    don't retry this task, the idea is to be alerted of failures
    """
    from apps.alerts.models import AlertGroup

    now = timezone.now()
    two_days_ago = now - datetime.timedelta(days=2)

    alert_groups = AlertGroup.objects.using(get_random_readonly_database_key_if_present_otherwise_default()).filter(
        ~Q(silenced=True, silenced_until__isnull=True),  # filter silenced forever alert_groups
        # here we should query maintenance_uuid rather than joining on channel__integration
        # and checking for something like ~Q(channel__integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE)
        # this avoids an unnecessary join
        maintenance_uuid__isnull=True,
        is_escalation_finished=False,
        resolved=False,
        acknowledged=False,
        root_alert_group=None,
        started_at__range=(two_days_ago, now),
    )

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

    if alert_group_ids_that_failed_audit:
        msg = f"The following alert group id(s) failed auditing: {', '.join(alert_group_ids_that_failed_audit)}"

        task_logger.warning(msg)
        raise AlertGroupEscalationPolicyExecutionAuditException(msg)

    task_logger.info("There were no alert groups that failed auditing")
    send_alert_group_escalation_auditor_task_heartbeat()
