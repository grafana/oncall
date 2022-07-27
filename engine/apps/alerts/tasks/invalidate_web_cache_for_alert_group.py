from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def invalidate_web_cache_for_alert_group(org_pk=None, channel_pk=None, alert_group_pk=None, alert_group_pks=None):
    # todo: remove
    pass
