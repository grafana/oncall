import logging
from typing import Optional

from celery.utils.log import get_task_logger

from apps.alerts.escalation_snapshot.serializers import EscalationSnapshotSerializer
from apps.alerts.escalation_snapshot.snapshot_classes.escalation_policy_snapshot import EscalationPolicySnapshot
from apps.alerts.models.alert_group_log_record import AlertGroupLogRecord

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


class EscalationSnapshot:
    __slots__ = (
        "alert_group",
        "channel_filter_snapshot",
        "escalation_chain_snapshot",
        "escalation_policies_snapshots",
        "last_active_escalation_policy_order",
        "slack_channel_id",
        "next_step_eta",
        "stop_escalation",
        "pause_escalation",
    )

    serializer = EscalationSnapshotSerializer

    def __init__(
        self,
        alert_group,
        channel_filter_snapshot,
        escalation_chain_snapshot,
        last_active_escalation_policy_order,
        escalation_policies_snapshots,
        slack_channel_id,
        pause_escalation,
        next_step_eta,
    ):
        self.alert_group = alert_group
        self.channel_filter_snapshot = channel_filter_snapshot  # ChannelFilterSnapshot object
        self.escalation_chain_snapshot = escalation_chain_snapshot  # EscalationChainSnapshot object
        self.last_active_escalation_policy_order = last_active_escalation_policy_order
        self.escalation_policies_snapshots = escalation_policies_snapshots  # list of EscalationPolicySnapshot objects
        self.slack_channel_id = slack_channel_id
        self.pause_escalation = pause_escalation
        self.next_step_eta = next_step_eta
        self.stop_escalation = False

    @property
    def last_active_escalation_policy_snapshot(self) -> Optional[EscalationPolicySnapshot]:
        order = self.last_active_escalation_policy_order
        if order is None:
            return None
        return self.escalation_policies_snapshots[order]

    @property
    def next_active_escalation_policy_snapshot(self) -> Optional[EscalationPolicySnapshot]:
        order = self.next_active_escalation_policy_order
        if len(self.escalation_policies_snapshots) < order + 1:
            next_link = None
        else:
            next_link = self.escalation_policies_snapshots[order]
        return next_link

    @property
    def next_active_escalation_policy_order(self) -> int:
        if self.last_active_escalation_policy_order is None:
            next_order = 0
        else:
            next_order = self.last_active_escalation_policy_order + 1
        return next_order

    def save_to_alert_group(self) -> None:
        self.alert_group.raw_escalation_snapshot = self.convert_to_dict()
        self.alert_group.save(update_fields=["raw_escalation_snapshot"])

    def convert_to_dict(self) -> dict:
        return self.serializer(self).data

    def execute_actual_escalation_step(self) -> None:
        """
        Executes actual escalation step and saves result of execution like stop_escalation param and eta,
        that will be used for start next escalate_alert_group task.
        Also updates self.last_active_escalation_policy_order if escalation step was executed.
        :return: None
        """
        escalation_policy_snapshot = self.next_active_escalation_policy_snapshot
        if escalation_policy_snapshot is None:
            AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FINISHED,
                alert_group=self.alert_group,
                reason="escalation finished",
            ).save()
            self.stop_escalation = True
            logger.debug(
                "escalation_policy_snapshot is None, stop escalation. Last escalation policy snapshot order "
                f"{self.last_active_escalation_policy_order}"
            )
        else:
            logger.debug(
                f"Starting to execute escalation step {escalation_policy_snapshot.step_display} with order "
                f"{escalation_policy_snapshot.order}"
            )

            reason = f"lifecycle rule for {self.channel_filter_snapshot.str_for_clients} route"

            # get execution result in namedtuple format and save its data
            # (e.g. StepExecutionResultData(eta=None, start_from_beginning=False, stop_escalation=False)
            execution_result = escalation_policy_snapshot.execute(alert_group=self.alert_group, reason=reason)

            self.next_step_eta = execution_result.eta
            self.stop_escalation = execution_result.stop_escalation  # result of STEP_FINAL_RESOLVE
            self.pause_escalation = execution_result.pause_escalation  # result of STEP_NOTIFY_IF_NUM_ALERTS_IN_WINDOW

            last_active_escalation_policy_order = escalation_policy_snapshot.order

            if execution_result.start_from_beginning:  # result of STEP_REPEAT_ESCALATION_N_TIMES
                last_active_escalation_policy_order = None

            # do not advance to the next escalation policy if escalation is paused
            if execution_result.pause_escalation:
                last_active_escalation_policy_order = self.last_active_escalation_policy_order

            self.last_active_escalation_policy_order = last_active_escalation_policy_order

            logger.debug(
                f"Finished to execute escalation step {escalation_policy_snapshot.step_display} with order "
                f"{escalation_policy_snapshot.order}, next escalation policy snapshot order "
                f"{self.next_active_escalation_policy_order}"
            )
