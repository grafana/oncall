import datetime
import logging
import typing

import pytz
from celery import uuid as celery_uuid
from dateutil.parser import parse
from django.apps import apps
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError

from apps.alerts.escalation_snapshot.snapshot_classes import (
    ChannelFilterSnapshot,
    EscalationChainSnapshot,
    EscalationPolicySnapshot,
    EscalationSnapshot,
)
from apps.alerts.tasks import escalate_alert_group

if typing.TYPE_CHECKING:
    from apps.alerts.models import ChannelFilter

logger = logging.getLogger(__name__)

# Is a delay to prevent intermediate activity by system in case user is doing some multi-step action.
# For example if user wants to unack and ack we don't need to launch escalation right after unack.
START_ESCALATION_DELAY = 10


class EscalationSnapshotMixin:
    """
    Mixin for AlertGroup. It contains methods related with alert group escalation
    """

    # TODO: add stricter typing
    # TODO: should this class actually be an AbstractBaseClass instead?
    raw_escalation_snapshot: dict | None
    channel_filter: typing.Optional["ChannelFilter"]

    def build_raw_escalation_snapshot(self) -> dict:
        """
        Builds new escalation chain in a json serializable format (dict).
        Use this method to prepare escalation chain data for saving to alert group before start new escalation.
        """
        data = {}

        if self.escalation_chain_exists:
            channel_filter: "ChannelFilter" = self.channel_filter
            escalation_chain = channel_filter.escalation_chain
            escalation_policies = escalation_chain.escalation_policies.all()

            data = {
                "channel_filter_snapshot": channel_filter,
                "escalation_chain_snapshot": escalation_chain,
                "escalation_policies_snapshots": escalation_policies,
                "slack_channel_id": self.slack_channel_id,
            }
        return EscalationSnapshot.serializer(data).data

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
    def channel_filter_snapshot(self) -> typing.Optional[ChannelFilterSnapshot]:
        """
        in some cases we need only channel filter and don't want to serialize whole escalation
        """
        escalation_snapshot = self.raw_escalation_snapshot
        if not escalation_snapshot:
            return None

        channel_filter_snapshot = escalation_snapshot["channel_filter_snapshot"]
        if not channel_filter_snapshot:
            return None

        channel_filter_snapshot = ChannelFilterSnapshot.serializer().to_internal_value(channel_filter_snapshot)
        return ChannelFilterSnapshot(**channel_filter_snapshot)

    @cached_property
    def escalation_chain_snapshot(self) -> typing.Optional[EscalationChainSnapshot]:
        """
        in some cases we need only escalation chain and don't want to serialize whole escalation
        escalation_chain_snapshot_object = None
        """
        escalation_snapshot = self.raw_escalation_snapshot
        if not escalation_snapshot:
            return None

        escalation_chain_snapshot = escalation_snapshot["escalation_chain_snapshot"]
        if not escalation_chain_snapshot:
            return None

        escalation_chain_snapshot = EscalationChainSnapshot.serializer().to_internal_value(escalation_chain_snapshot)
        return EscalationChainSnapshot(**escalation_chain_snapshot)

    @cached_property
    def escalation_snapshot(self) -> typing.Optional[EscalationSnapshot]:
        raw_escalation_snapshot = self.raw_escalation_snapshot
        if raw_escalation_snapshot:
            try:
                return self._deserialize_escalation_snapshot(raw_escalation_snapshot)
            except ValidationError as e:
                logger.error(f"Error trying to deserialize raw escalation snapshot: {e}")
        return None

    @cached_property
    def has_escalation_policies_snapshots(self) -> bool:
        if not self.raw_escalation_snapshot:
            return False
        return len(self.raw_escalation_snapshot["escalation_policies_snapshots"]) > 0

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
    def escalation_chain_exists(self) -> bool:
        if self.pause_escalation:
            return False
        elif not self.channel_filter:
            return False
        return self.channel_filter.escalation_chain is not None

    @property
    def pause_escalation(self) -> bool:
        """
        get pause_escalation field directly to avoid serialization overhead
        """
        if not self.raw_escalation_snapshot:
            return False
        return self.raw_escalation_snapshot.get("pause_escalation", False)

    @property
    def next_step_eta(self) -> typing.Optional[datetime.datetime]:
        """
        get next_step_eta field directly to avoid serialization overhead
        """
        if not self.raw_escalation_snapshot:
            return None

        raw_next_step_eta = self.raw_escalation_snapshot.get("next_step_eta")
        return None if not raw_next_step_eta else parse(raw_next_step_eta).replace(tzinfo=pytz.UTC)

    def start_escalation_if_needed(self, countdown=START_ESCALATION_DELAY, eta=None):
        """
        :type self:AlertGroup
        """
        AlertGroup = apps.get_model("alerts", "AlertGroup")

        is_on_maintenace_or_debug_mode = self.channel.maintenance_mode is not None

        if (
            self.is_restricted
            or is_on_maintenace_or_debug_mode
            or self.pause_escalation
            or not self.escalation_chain_exists
        ):
            logger.debug(
                f"Not escalating alert group w/ pk: {self.pk}\n"
                f"is_restricted: {self.is_restricted}\n"
                f"is_on_maintenace_or_debug_mode: {is_on_maintenace_or_debug_mode}\n"
                f"pause_escalation: {self.pause_escalation}\n"
                f"escalation_chain_exists: {self.escalation_chain_exists}"
            )
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
        escalate_alert_group.apply_async((self.pk,), countdown=countdown, immutable=True, eta=eta, task_id=task_id)

    def stop_escalation(self):
        self.is_escalation_finished = True
        # change active_escalation_id to prevent alert escalation
        self.active_escalation_id = "intentionally_stopped"
        self.save(update_fields=["is_escalation_finished", "active_escalation_id"])
