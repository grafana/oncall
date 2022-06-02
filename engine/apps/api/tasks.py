from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.core.cache import cache

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


def get_cache_key_caching_alert_group_for_web(alert_group_pk):
    CACHE_KEY_PREFIX = "cache_alert_group_for_web"
    return f"{CACHE_KEY_PREFIX}_{alert_group_pk}"


# TODO: remove this tasks after all of them will be processed in prod
@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def schedule_cache_for_alert_group(alert_group_pk):
    CACHE_FOR_ALERT_GROUP_LIFETIME = 60
    START_CACHE_DELAY = 5  # we introduce delay to avoid recaching after each alert.

    task = cache_alert_group_for_web.apply_async(args=[alert_group_pk], countdown=START_CACHE_DELAY)
    cache_key = get_cache_key_caching_alert_group_for_web(alert_group_pk)
    cache.set(cache_key, task.id, timeout=CACHE_FOR_ALERT_GROUP_LIFETIME)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def cache_alert_group_for_web(alert_group_pk):
    """
    Async task to re-cache alert_group for web.
    """
    cache_key = get_cache_key_caching_alert_group_for_web(alert_group_pk)
    cached_task_id = cache.get(cache_key)
    current_task_id = cache_alert_group_for_web.request.id

    if cached_task_id is None:
        return (
            f"cache_alert_group_for_web skipped, because of current task_id ({current_task_id})"
            f" for alert_group {alert_group_pk} doesn't exist in cache, which means this task is not"
            f" relevant: cache was dropped by engine restart ot CACHE_FOR_ALERT_GROUP_LIFETIME"
        )
    if not current_task_id == cached_task_id or cached_task_id is None:
        return (
            f"cache_alert_group_for_web skipped, because of current task_id ({current_task_id})"
            f" doesn't equal to cached task_id ({cached_task_id}) for alert_group {alert_group_pk},"
        )
    else:
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        alert_group = AlertGroup.all_objects.using_readonly_db.get(pk=alert_group_pk)
        alert_group.cache_for_web(alert_group.channel.organization)
        logger.info(f"cache_alert_group_for_web: cache refreshed for alert_group {alert_group_pk}")
