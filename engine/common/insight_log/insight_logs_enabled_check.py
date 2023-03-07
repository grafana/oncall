import logging

from django.conf import settings
from django.core.cache import cache

from apps.grafana_plugin.helpers import GcomAPIClient

logger = logging.getLogger(__name__)


def is_insight_logs_enabled(organization):
    """
    is_insight_logs_enabled checks if inside logs enabled for given organization.
    """
    CACHE_KEY = f"insight_logs_{organization.id}"
    insight_logs_enabled = cache.get(CACHE_KEY, None)
    if insight_logs_enabled is None:
        logger.info(f"is_insight_logs_enabled: check if logs enabled for org_id={organization.id}")
        client = GcomAPIClient(organization.gcom_token)
        cluster_slug = client.get_cluster_slug(organization.stack_id, timeout=5)
        logger.info(
            "is_insight_logs_enabled: "
            f"IS_OPEN_SOURCE={settings.IS_OPEN_SOURCE} "
            f"ONCALL_BACKEND_REGION={settings.ONCALL_BACKEND_REGION} "
            f"cluster_slug={cluster_slug}"
        )
        insight_logs_enabled = settings.IS_OPEN_SOURCE or settings.ONCALL_BACKEND_REGION == cluster_slug
        logger.info(f"is_insight_logs_enabled: insight_logs {insight_logs_enabled}")
        cache.set(CACHE_KEY, insight_logs_enabled, 60 * 60 * 24)
    return insight_logs_enabled
