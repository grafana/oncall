import typing
from urllib.parse import urljoin

from django.db import models

from common.constants.plugin_ids import PluginID

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, ChannelFilter
    from apps.user_management.models import Organization


def get_incident_url(organization, incident_id) -> str:
    return urljoin(organization.grafana_url, f"a/{PluginID.INCIDENT}/incidents/{incident_id}")


class RelatedIncident(models.Model):
    attached_alert_groups: "RelatedManager['AlertGroup']"
    channel_filter: typing.Optional["ChannelFilter"]
    organization: "Organization"

    incident_id = models.CharField(db_index=True, max_length=50)
    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="related_incidents",
    )
    channel_filter = models.ForeignKey(
        "alerts.ChannelFilter",
        on_delete=models.SET_NULL,
        null=True,
        related_name="related_incidents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    attached_alert_groups = models.ManyToManyField(
        "alerts.AlertGroup",
        related_name="related_incidents",
    )

    class Meta:
        unique_together = ("organization", "incident_id")

    def get_incident_link(self) -> str:
        return get_incident_url(self.organization, self.incident_id)
