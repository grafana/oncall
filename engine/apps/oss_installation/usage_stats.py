import logging
import platform
from dataclasses import asdict, dataclass

import requests
from django.conf import settings
from django.db.models import Sum

from apps.alerts.models import AlertGroupCounter
from apps.oss_installation.utils import active_oss_users_count

USAGE_STATS_URL = "https://stats.grafana.org/oncall-usage-report"
USAGE_STATS_HTTP_TIMEOUT = 500

logger = logging.getLogger(__name__)


@dataclass
class UsageStatsReport:
    version: str
    os: str
    arch: str
    usage_stats_id: str
    metrics: dict


class UsageStatsService:
    def get_usage_stats_report(self):
        from apps.oss_installation.models import OssInstallation

        metrics = {}
        metrics["active_users_count"] = active_oss_users_count()
        total_alert_groups = AlertGroupCounter.objects.aggregate(Sum("value")).get("value__sum", None)
        if total_alert_groups is None:
            total_alert_groups = 0
        metrics["alert_groups_count"] = total_alert_groups

        usage_stats_id = OssInstallation.objects.get_or_create()[0].installation_id

        return UsageStatsReport(
            usage_stats_id=str(usage_stats_id),
            os=platform.system(),
            arch=platform.machine(),
            version=settings.VERSION,
            metrics=metrics,
        )

    def send_usage_stats_report(self):
        report = self.get_usage_stats_report()
        try:
            requests.post(url=USAGE_STATS_URL, json=asdict(report), timeout=USAGE_STATS_HTTP_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logging.info(f"Failed to send_usage_stats_report. msg={str(e)}")
