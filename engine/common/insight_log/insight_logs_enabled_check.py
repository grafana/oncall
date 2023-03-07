from django.conf import settings
from django.core.cache import cache

from apps.grafana_plugin.helpers import GcomAPIClient


def is_insight_logs_enabled(organization):
    """
    is_insight_logs_enabled checks if inside logs enabled for given organization.
    """
    CACHE_KEY = f"insight_logs_{organization.id}"
    insight_logs_enabled = cache.get(CACHE_KEY, None)
    if insight_logs_enabled is None:
        client = GcomAPIClient(organization.gcom_token)
        cluster_slug = client.get_cluster_slug(organization.stack_id, timeout=5)
        insight_logs_enabled = settings.IS_OPEN_SOURCE or settings.ONCALL_BACKEND_REGION == cluster_slug
        cache.set(CACHE_KEY, insight_logs_enabled, 60 * 60 * 24)
    return insight_logs_enabled
