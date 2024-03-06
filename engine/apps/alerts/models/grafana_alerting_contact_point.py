import logging

from django.db import models

logger = logging.getLogger(__name__)


# deprecated
class GrafanaAlertingContactPoint(models.Model):
    GRAFANA_CONTACT_POINT = "grafana"
    ALERTING_DATASOURCE = "alertmanager"

    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="contact_points",
    )
    uid = models.CharField(max_length=100, null=True, default=None)  # receiver uid is None for non-Grafana datasource
    name = models.CharField(max_length=100)
    datasource_name = models.CharField(max_length=100, default="grafana")
    datasource_id = models.IntegerField(null=True, default=None)  # id is None for Grafana datasource
    datasource_uid = models.CharField(max_length=100, null=True, default=None)  # uid is None for Grafana datasource
