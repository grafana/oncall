import datetime
import typing

import requests
from celery import shared_task
from django.apps import apps
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
        task_logger.info(f"Skipping sending heartbeat as no heartbeat URL is configured")


def audit_alert_group_escalation(alert_group: "AlertGroup") -> None:
    escalation_snapshot = alert_group.escalation_snapshot
    alert_group_id = alert_group.id
    base_msg = f"Alert group {alert_group_id}"

    if not escalation_snapshot:
        raise AlertGroupEscalationPolicyExecutionAuditException(
            f"{base_msg} does not have an escalation snapshot associated with it, this should never occur"
        )
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
        return
    task_logger.info(
        f"{base_msg}'s escalation snapshot has {num_of_executed_escalation_policy_snapshots} executed escalation policies"
    )

    for executed_escalation_policy_snapshot in executed_escalation_policy_snapshots:
        escalation_policy_id = executed_escalation_policy_snapshot.id

        # TODO: is it valid to only check for the finished log record type here?
        if not executed_escalation_policy_snapshot.has_finished_log_record(alert_group_id):
            raise AlertGroupEscalationPolicyExecutionAuditException(
                f"{base_msg}'s escalation policy snapshot {escalation_policy_id} does not have a finished alert group log record associated with it"
            )

        task_logger.info(
            f"{base_msg}'s escalation policy snapshot {escalation_policy_id} has a finished alert group log record associated with it"
        )

    task_logger.info(f"{base_msg} passed the audit checks")


def get_auditable_alert_groups_started_at_range() -> typing.Tuple[datetime.datetime, datetime.datetime]:
    """
    NOTE: this started_at__range is a bit of a hack..
    we wanted to avoid performing a migration on the alerts_alertgroup table to update
    alert groups where raw_escalation_snapshot was None. raw_escalation_snapshot being None is a legitimate case,
    where the alert group's integration does not have an escalation chain associated with it.

    However, we wanted a way to be able to differentiate between "actually None" and "there was an error writing to
    raw_escalation_snapshot" (as this is performed async by a celery task).

    This field was updated, in the commit that added this comment, to no longer be set to None by default.
    As part of this celery task we do a check that this field is in fact not None, so if we were to check older
    alert groups, whose integration did not have an escalation chain at the time the alert group was created
    we would raise errors
    """
    return (datetime.datetime(2023, 2, 5), timezone.now() - timezone.timedelta(days=2))


# don't retry this task as the AlertGroup DB query is rather expensive
@shared_task
def check_escalation_finished_task():
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

    alert_groups = AlertGroup.all_objects.using(get_random_readonly_database_key_if_present_otherwise_default()).filter(
        ~Q(channel__integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE),
        ~Q(silenced=True, silenced_until__isnull=True),  # filter silenced forever alert_groups
        is_escalation_finished=False,
        resolved=False,
        acknowledged=False,
        root_alert_group=None,
        started_at__range=get_auditable_alert_groups_started_at_range(),
    )

    if not alert_groups.exists():
        task_logger.info("There are no alert groups to audit, everything is good :)")

    for alert_group in alert_groups:
        audit_alert_group_escalation(alert_group)

    send_alert_group_escalation_auditor_task_heartbeat()
