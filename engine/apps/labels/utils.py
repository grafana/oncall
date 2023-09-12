import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def is_labels_enabled(organization):
    """
    is_labels_enabled checks if oncall is deployed on same cluster that its grafana instance.
    Replace with feature flag when cross cluster requests are available for labels plugin
    """
    logger.info(
        "is_labels_enabled: "
        f"FEATURE_LABELS_ENABLED={settings.FEATURE_LABELS_ENABLED} "
        f"ONCALL_BACKEND_REGION={settings.ONCALL_BACKEND_REGION} "
        f"cluster_slug={organization.cluster_slug}"
    )
    return settings.FEATURE_LABELS_ENABLED and settings.ONCALL_BACKEND_REGION == organization.cluster_slug
