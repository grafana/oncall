import typing
from urllib.parse import urljoin

from django.db import models

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, ChannelFilter
    from apps.user_management.models import Organization


def get_incident_url(organization, incident_id) -> str:
    return urljoin(organization.grafana_url, f"a/grafana-incident-app/incidents/{incident_id}")


class DeclaredIncident(models.Model):
    attached_alert_groups: "RelatedManager['AlertGroup']"
    channel_filter: typing.Optional["ChannelFilter"]
    organization: "Organization"

    incident_id = models.CharField(db_index=True, max_length=50)
    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="declared_incidents",
    )
    channel_filter = models.ForeignKey(
        "alerts.ChannelFilter",
        on_delete=models.SET_NULL,
        null=True,
        related_name="declared_incidents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def get_incident_link(self) -> str:
        return get_incident_url(self.organization, self.incident_id)
