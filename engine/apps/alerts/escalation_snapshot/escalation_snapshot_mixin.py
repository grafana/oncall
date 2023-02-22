import logging
from typing import Optional

import pytz
from celery import uuid as celery_uuid
from dateutil.parser import parse
from django.apps import apps
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.alerts.escalation_snapshot.snapshot_classes import (
    ChannelFilterSnapshot,
    EscalationChainSnapshot,
    EscalationPolicySnapshot,
    EscalationSnapshot,
)
from apps.alerts.escalation_snapshot.utils import eta_for_escalation_step_notify_if_time
from apps.alerts.tasks import calculate_escalation_finish_time, escalate_alert_group

logger = logging.getLogger(__name__)

# Is a delay to prevent intermediate activity by system in case user is doing some multi-step action.
# For example if user wants to unack and ack we don't need to launch escalation right after unack.
START_ESCALATION_DELAY = 10


class EscalationSnapshotMixin:
    """
    Mixin for AlertGroup. It contains methods related with alert group escalation
    """

    def build_raw_escalation_snapshot(self) -> dict:
        """
        Builds new escalation chain in a json serializable format (dict).
        Use this method to prepare escalation chain data for saving to alert group before start new escalation.

        Example result:
        {
            'channel_filter_snapshot': {
                'id': 1,
                'notify_in_slack': True,
                'str_for_clients': 'default',
                'notify_in_telegram': True
            },
            'escalation_chain_snapshot': {
                'id': 1,
                'name': 'Test'
            },
            'escalation_policies_snapshots': [
                {
                    'id': 1,
                    'step': 14,
                    'order': 0,
                    'to_time': None,
                    'from_time': None,
                    'num_alerts_in_window': None,
                    'num_minutes_in_window': None,
                    'wait_delay': None,
                    'notify_schedule': None,
                    'notify_to_group': None,
                    'passed_last_time': None,
                    'escalation_counter': 0,
                    'last_notified_user': None,
                    'custom_button_trigger': None,
                    'notify_to_users_queue': [1,2,3]
                },
                {
                    'id': 2,
                    'step': 0,
                    'order': 1,
                    'to_time': None,
                    'from_time': None,
                    'num_alerts_in_window': None,
                    'num_minutes_in_window': None,
                    'wait_delay': '00:05:00',
                    'notify_schedule': None,
                    'notify_to_group': None,
                    'passed_last_time': None,
                    'escalation_counter': 0,
                    'last_notified_user': None,
                    'custom_button_trigger': None,
                    'notify_to_users_queue': []
                },
            ],
            'slack_channel_id': 'SLACK_CHANNEL_ID',
            'last_active_escalation_policy_order': None,
            'pause_escalation': False,
            'next_step_eta': '2021-10-18T10:28:28.890369Z
        }
        """

        escalation_snapshot = None

        if self.escalation_chain_exists:
            channel_filter = self.channel_filter
            escalation_chain = channel_filter.escalation_chain
            escalation_policies = escalation_chain.escalation_policies.all()

            data = {
                "channel_filter_snapshot": channel_filter,
                "escalation_chain_snapshot": escalation_chain,
                "escalation_policies_snapshots": escalation_policies,
                "slack_channel_id": self.slack_channel_id,
            }
            escalation_snapshot = EscalationSnapshot.serializer(data).data
        return escalation_snapshot

    def calculate_eta_for_finish_escalation(self, escalation_started=False, start_time=None):
        if not self.escalation_snapshot:
            return
        EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")
        TOLERANCE_SECONDS = 1
        TOLERANCE_TIME = timezone.timedelta(seconds=NEXT_ESCALATION_DELAY + TOLERANCE_SECONDS)
        start_time = start_time or timezone.now()  # start time may be different for silenced incidents
        wait_summ = timezone.timedelta()
        # Get next_active_escalation_policy_order using flag `escalation_started` because this calculation can be
        # started in parallel with escalation task where next_active_escalation_policy_order can be changed.
        # That's why we are using `escalation_started` flag here, which means, that we want count eta from the first
        # step.
        next_escalation_policy_order = (
            self.escalation_snapshot.next_active_escalation_policy_order if escalation_started else 0
        )
        escalation_policies = self.escalation_snapshot.escalation_policies_snapshots[next_escalation_policy_order:]
        for escalation_policy in escalation_policies:
            if escalation_policy.step == EscalationPolicy.STEP_WAIT:
                if escalation_policy.wait_delay is not None:
                    wait_summ += escalation_policy.wait_delay
                else:
                    wait_summ += EscalationPolicy.DEFAULT_WAIT_DELAY  # Default wait in case it's not selected yet
            elif escalation_policy.step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
                if escalation_policy.from_time and escalation_policy.to_time:
                    estimate_start_time = start_time + wait_summ
                    STEP_TOLERANCE = timezone.timedelta(minutes=1)
                    next_step_estimate_start_time = eta_for_escalation_step_notify_if_time(
                        escalation_policy.from_time,
                        escalation_policy.to_time,
                        estimate_start_time + STEP_TOLERANCE,
                    )
                    wait_summ += next_step_estimate_start_time - estimate_start_time
            elif escalation_policy.step == EscalationPolicy.STEP_REPEAT_ESCALATION_N_TIMES:
                # the part of escalation with repeat step will be passed six times: the first time plus five repeats
                wait_summ *= EscalationPolicy.MAX_TIMES_REPEAT + 1
            elif escalation_policy.step == EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
                # In this case we cannot calculate finish time, so we return None
                return
            elif escalation_policy.step == EscalationPolicy.STEP_FINAL_RESOLVE:
                break
            wait_summ += TOLERANCE_TIME

        escalation_finish_time = start_time + wait_summ
        return escalation_finish_time

    @property
    def channel_filter_with_respect_to_escalation_snapshot(self):
        # Try to get saved channel filter data from escalation snapshot at first because channel filter object
        # can be changed or deleted during escalation
        return self.channel_filter_snapshot or self.channel_filter

    @property
    def escalation_chain_with_respect_to_escalation_snapshot(self):
        # Try to get saved escalation chain data from escalation snapshot at first because escalation chain object
        # can be changed or deleted during escalation
        return self.escalation_chain_snapshot or (self.channel_filter.escalation_chain if self.channel_filter else None)

    @cached_property
    def channel_filter_snapshot(self) -> Optional[ChannelFilterSnapshot]:
        # in some cases we need only channel filter and don't want to serialize whole escalation
        channel_filter_snapshot_object = None
        escalation_snapshot = self.raw_escalation_snapshot
        if escalation_snapshot is not None:
            channel_filter_snapshot = ChannelFilterSnapshot.serializer().to_internal_value(
                escalation_snapshot["channel_filter_snapshot"]
            )
            channel_filter_snapshot_object = ChannelFilterSnapshot(**channel_filter_snapshot)
        return channel_filter_snapshot_object

    @cached_property
    def escalation_chain_snapshot(self) -> Optional[EscalationChainSnapshot]:
        # in some cases we need only escalation chain and don't want to serialize whole escalation
        escalation_chain_snapshot_object = None
        escalation_snapshot = self.raw_escalation_snapshot
        if escalation_snapshot is not None:
            escalation_chain_snapshot = EscalationChainSnapshot.serializer().to_internal_value(
                escalation_snapshot["escalation_chain_snapshot"]
            )
            escalation_chain_snapshot_object = EscalationChainSnapshot(**escalation_chain_snapshot)
        return escalation_chain_snapshot_object

    @cached_property
    def escalation_snapshot(self) -> Optional[EscalationSnapshot]:
        escalation_snapshot_object = None
        raw_escalation_snapshot = self.raw_escalation_snapshot
        if raw_escalation_snapshot is not None:
            try:
                escalation_snapshot_object = self._deserialize_escalation_snapshot(raw_escalation_snapshot)
            except ValidationError as e:
                logger.error(f"Error trying to deserialize raw escalation snapshot: {e}")
        return escalation_snapshot_object

    def _deserialize_escalation_snapshot(self, raw_escalation_snapshot) -> EscalationSnapshot:
        """
        Deserializes raw escalation snapshot to EscalationSnapshot object with channel_filter_snapshot as
        ChannelFilterSnapshot object and escalation_policies_snapshots as EscalationPolicySnapshot objects
        :param raw_escalation_snapshot: dict
        :return: EscalationSnapshot
        """
        deserialized_escalation_snapshot = EscalationSnapshot.serializer().to_internal_value(raw_escalation_snapshot)
        channel_filter_snapshot = deserialized_escalation_snapshot["channel_filter_snapshot"]
        deserialized_escalation_snapshot["channel_filter_snapshot"] = ChannelFilterSnapshot(**channel_filter_snapshot)

        escalation_chain_snapshot = deserialized_escalation_snapshot["escalation_chain_snapshot"]
        deserialized_escalation_snapshot["escalation_chain_snapshot"] = EscalationChainSnapshot(
            **escalation_chain_snapshot
        )

        escalation_policies_snapshots_raw = deserialized_escalation_snapshot["escalation_policies_snapshots"]
        escalation_policies_snapshots = []
        for escalation_policy_snapshot in escalation_policies_snapshots_raw:
            escalation_policies_snapshots.append(EscalationPolicySnapshot(**escalation_policy_snapshot))
        deserialized_escalation_snapshot["escalation_policies_snapshots"] = escalation_policies_snapshots

        escalation_snapshot_object = EscalationSnapshot(self, **deserialized_escalation_snapshot)
        return escalation_snapshot_object

    @property
    def escalation_chain_exists(self):
        return not self.pause_escalation and self.channel_filter and self.channel_filter.escalation_chain

    @property
    def pause_escalation(self):
        # get pause_escalation field directly to avoid serialization overhead
        return self.raw_escalation_snapshot is not None and self.raw_escalation_snapshot.get("pause_escalation", False)

    @property
    def next_step_eta(self):
        # get next_step_eta field directly to avoid serialization overhead
        raw_next_step_eta = (
            self.raw_escalation_snapshot.get("next_step_eta") if self.raw_escalation_snapshot is not None else None
        )
        if raw_next_step_eta:
            return parse(raw_next_step_eta).replace(tzinfo=pytz.UTC)

    def start_escalation_if_needed(self, countdown=START_ESCALATION_DELAY, eta=None):
        """
        :type self:AlertGroup
        """
        AlertGroup = apps.get_model("alerts", "AlertGroup")

        is_on_maintenace_or_debug_mode = (
            self.channel.maintenance_mode is not None or self.channel.organization.maintenance_mode is not None
        )
        if is_on_maintenace_or_debug_mode:
            return
        if self.pause_escalation:
            return

        if not self.escalation_chain_exists:
            return

        logger.debug(f"Start escalation for alert group with pk: {self.pk}")

        # take raw escalation snapshot from db if escalation is paused
        raw_escalation_snapshot = (
            self.build_raw_escalation_snapshot() if not self.pause_escalation else self.raw_escalation_snapshot
        )
        task_id = celery_uuid()

        AlertGroup.all_objects.filter(pk=self.pk,).update(
            active_escalation_id=task_id,
            is_escalation_finished=False,
            raw_escalation_snapshot=raw_escalation_snapshot,
        )
        if not self.pause_escalation:
            calculate_escalation_finish_time.apply_async((self.pk,), immutable=True)
        escalate_alert_group.apply_async((self.pk,), countdown=countdown, immutable=True, eta=eta, task_id=task_id)

    def stop_escalation(self):
        self.is_escalation_finished = True
        self.estimate_escalation_finish_time = None
        # change active_escalation_id to prevent alert escalation
        self.active_escalation_id = "intentionally_stopped"
        self.save(update_fields=["is_escalation_finished", "estimate_escalation_finish_time", "active_escalation_id"])
