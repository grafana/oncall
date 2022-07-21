from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def invalidate_web_cache_for_alert_group(org_pk=None, channel_pk=None, alert_group_pk=None, alert_group_pks=None):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    DynamicSetting = apps.get_model("base", "DynamicSetting")

    if channel_pk:
        task_logger.debug(f"invalidate_web_cache_for_alert_group: Reason - alert_receive_channel {channel_pk}")
        q = AlertGroup.all_objects.filter(channel__pk=channel_pk)
    elif org_pk:
        task_logger.debug(f"invalidate_web_cache_for_alert_group: Reason - organization {org_pk}")
        q = AlertGroup.all_objects.filter(channel__organization__pk=org_pk)
    elif alert_group_pk:
        task_logger.debug(f"invalidate_web_cache_for_alert_group: Reason - alert_group {alert_group_pk}")
        q = AlertGroup.all_objects.filter(pk=alert_group_pk)
    elif alert_group_pks:
        task_logger.debug(f"invalidate_web_cache_for_alert_group: Reason - alert_groups {alert_group_pks}")
        q = AlertGroup.all_objects.filter(pk__in=alert_group_pks)

    skip_task = DynamicSetting.objects.get_or_create(name="skip_invalidate_web_cache_for_alert_group")[0]
    if skip_task.boolean_value:
        return "Task has been skipped because of skip_invalidate_web_cache_for_alert_group DynamicSetting"
    q.update(cached_render_for_web={})
