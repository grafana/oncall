from uuid import uuid4

import humanize
import pytz
from django.apps import apps
from django.db import models, transaction
from django.utils import timezone

from apps.slack.scenarios.scenario_step import ScenarioStep
from common.exceptions import MaintenanceCouldNotBeStartedError
from common.insight_log import MaintenanceEvent, write_maintenance_insight_log


class MaintainableObject(models.Model):
    class Meta:
        abstract = True

    DURATION_ONE_HOUR = timezone.timedelta(hours=1)
    DURATION_THREE_HOURS = timezone.timedelta(hours=3)
    DURATION_SIX_HOURS = timezone.timedelta(hours=6)
    DURATION_TWELVE_HOURS = timezone.timedelta(hours=12)
    DURATION_TWENTY_FOUR_HOURS = timezone.timedelta(hours=24)

    MAINTENANCE_DURATION_CHOICES = (
        (DURATION_ONE_HOUR, "1 hour"),
        (DURATION_THREE_HOURS, "3 hours"),
        (DURATION_SIX_HOURS, "6 hours"),
        (DURATION_TWELVE_HOURS, "12 hours"),
        (DURATION_TWENTY_FOUR_HOURS, "24 hours"),
    )

    maintenance_duration = models.DurationField(default=None, null=True, choices=MAINTENANCE_DURATION_CHOICES)
    (DEBUG_MAINTENANCE, MAINTENANCE) = range(2)

    DEBUG_MAINTENANCE_KEY = "Debug"
    MAINTENANCE_KEY = "Maintenance"

    MAINTENANCE_MODE_CHOICES = ((DEBUG_MAINTENANCE, DEBUG_MAINTENANCE_KEY), (MAINTENANCE, MAINTENANCE_KEY))
    MAINTENANCE_VERBAL = {
        DEBUG_MAINTENANCE: "Debug (silence all escalations)",
        MAINTENANCE: "Maintenance (collect everything in one incident)",
    }

    maintenance_mode = models.IntegerField(default=None, null=True, choices=MAINTENANCE_MODE_CHOICES)

    maintenance_uuid = models.CharField(max_length=250, unique=True, null=True, default=None)
    maintenance_started_at = models.DateTimeField(null=True, default=None)
    maintenance_author = models.ForeignKey(
        "user_management.user", on_delete=models.SET_NULL, null=True, related_name="%(class)s_maintenances_created"
    )

    def start_disable_maintenance_task(self, countdown):
        raise NotImplementedError

    def get_organization(self):
        raise NotImplementedError

    def get_team(self):
        raise NotImplementedError

    def get_verbal(self):
        raise NotImplementedError

    def force_disable_maintenance(self, user):
        raise NotImplementedError

    def notify_about_maintenance_action(self, text, send_to_general_log_channel=True):
        raise NotImplementedError

    def send_maintenance_incident(self, organization, group, alert):
        slack_team_identity = organization.slack_team_identity
        if slack_team_identity is not None:
            channel_id = organization.general_log_channel_id
            attachments = group.render_slack_attachments()
            blocks = group.render_slack_blocks()
            AlertShootingStep = ScenarioStep.get_step("distribute_alerts", "AlertShootingStep")
            AlertShootingStep(slack_team_identity, organization).publish_slack_messages(
                slack_team_identity, group, alert, attachments, channel_id, blocks
            )

    def start_maintenance(self, mode, maintenance_duration, user):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
        Alert = apps.get_model("alerts", "Alert")

        with transaction.atomic():
            _self = self.__class__.objects.select_for_update().get(pk=self.pk)
            if _self.maintenance_mode is not None:
                raise MaintenanceCouldNotBeStartedError("Already on maintenance")
            organization = _self.get_organization()
            team = _self.get_team()
            verbal = _self.get_verbal()
            user_verbal = user.get_user_verbal_for_team_for_slack()
            duration_verbal = humanize.naturaldelta(maintenance_duration)
            # NOTE: there could be multiple maintenance integrations in case of a race condition
            # (no constraints at the db level, it shouldn't be an issue functionality-wise)
            maintenance_integration = AlertReceiveChannel.objects_with_maintenance.filter(
                organization=organization,
                team=team,
                integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE,
            ).last()
            if maintenance_integration is None:
                maintenance_integration = AlertReceiveChannel.create(
                    organization=organization,
                    team=team,
                    integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE,
                    author=user,
                )

            maintenance_uuid = _self.start_disable_maintenance_task(maintenance_duration)

            _self.maintenance_duration = timezone.timedelta(seconds=maintenance_duration)
            _self.maintenance_uuid = maintenance_uuid
            _self.maintenance_mode = mode
            _self.maintenance_started_at = timezone.now()
            _self.maintenance_author = user
            _self.save(
                update_fields=[
                    "maintenance_duration",
                    "maintenance_uuid",
                    "maintenance_mode",
                    "maintenance_started_at",
                    "maintenance_author",
                ]
            )
            self.maintenance_duration = _self.maintenance_duration
            self.maintenance_uuid = _self.maintenance_uuid
            self.maintenance_mode = _self.maintenance_mode
            self.maintenance_started_at = _self.maintenance_started_at
            self.maintenance_author = _self.maintenance_author
            if mode == AlertReceiveChannel.MAINTENANCE:
                group = AlertGroup.all_objects.create(
                    distinction=uuid4(),
                    web_title_cache=f"Maintenance of {verbal} for {maintenance_duration}",
                    maintenance_uuid=maintenance_uuid,
                    channel_filter_id=maintenance_integration.default_channel_filter.pk,
                    channel=maintenance_integration,
                )
                title = f"Maintenance of {verbal} for {duration_verbal}"
                message = (
                    f"Initiated by {user_verbal}."
                    f" During this time all alerts from integration will be collected here without escalations"
                )
                alert = Alert(
                    is_resolve_signal=False,
                    title=title,
                    message=message,
                    group=group,
                    raw_request_data={
                        "title": title,
                        "message": message,
                    },
                )
                alert.save()
        write_maintenance_insight_log(self, user, MaintenanceEvent.STARTED)
        if mode == AlertReceiveChannel.MAINTENANCE:
            self.send_maintenance_incident(organization, group, alert)
            self.notify_about_maintenance_action(
                f"Maintenance of {verbal}. Initiated by {user_verbal} for {duration_verbal}.",
                send_to_general_log_channel=False,
            )
        else:
            self.notify_about_maintenance_action(
                f"Debug of {verbal}. Initiated by {user_verbal} for {duration_verbal}."
            )

    @property
    def till_maintenance_timestamp(self):
        if self.maintenance_started_at is not None and self.maintenance_duration is not None:
            return int((self.maintenance_started_at + self.maintenance_duration).astimezone(pytz.UTC).timestamp())
        return None

    @property
    def started_at_timestamp(self):
        if self.maintenance_started_at is not None and self.maintenance_duration is not None:
            return int(self.maintenance_started_at.astimezone(pytz.UTC).timestamp())
        return None

    @classmethod
    def maintenance_duration_options_in_seconds(cls):
        options_in_seconds = []
        for ch in cls.MAINTENANCE_DURATION_CHOICES:
            options_in_seconds.append(int(ch[0].total_seconds()))
        return options_in_seconds
