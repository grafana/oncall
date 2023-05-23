import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def is_insight_logs_enabled(organization):
    """
    is_insight_logs_enabled checks if inside logs enabled for given organization.
    Now it checks if oncall is deployed on same cluster that its grafana instance to be able to forward logs
    to Loki through logs-forwarder.
    """
    logger.info(
        "is_insight_logs_enabled: "
        f"IS_OPEN_SOURCE={settings.IS_OPEN_SOURCE} "
        f"ONCALL_BACKEND_REGION={settings.ONCALL_BACKEND_REGION} "
        f"cluster_slug={organization.cluster_slug}"
    )
    return not settings.IS_OPEN_SOURCE and settings.ONCALL_BACKEND_REGION == organization.cluster_slug
