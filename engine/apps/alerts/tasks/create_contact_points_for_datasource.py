import logging

from celery.utils.log import get_task_logger
from django.core.cache import cache
from rest_framework import status

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def get_cache_key_create_contact_points_for_datasource(alert_receive_channel_id):
    CACHE_KEY_PREFIX = "create_contact_points_for_datasource"
    return f"{CACHE_KEY_PREFIX}_{alert_receive_channel_id}"


def set_cache_key_create_contact_points_for_datasource(alert_receive_channel_id, task_id):
    CACHE_LIFETIME = 600
    cache_key = get_cache_key_create_contact_points_for_datasource(alert_receive_channel_id)
    cache.set(cache_key, task_id, timeout=CACHE_LIFETIME)


@shared_dedicated_queue_retry_task
def schedule_create_contact_points_for_datasource(alert_receive_channel_id, datasource_list):
    START_TASK_DELAY = 3
    task = create_contact_points_for_datasource.apply_async(
        args=[alert_receive_channel_id, datasource_list], countdown=START_TASK_DELAY
    )
    set_cache_key_create_contact_points_for_datasource(alert_receive_channel_id, task.id)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def create_contact_points_for_datasource(alert_receive_channel_id, datasource_list):
    """
    Try to create contact points for other datasource.
    Restart task for datasource, for which contact point was not created.
    """
    cache_key = get_cache_key_create_contact_points_for_datasource(alert_receive_channel_id)
    cached_task_id = cache.get(cache_key)
    current_task_id = create_contact_points_for_datasource.request.id
    if cached_task_id is not None and current_task_id != cached_task_id:
        return

    from apps.alerts.models import AlertReceiveChannel

    alert_receive_channel = AlertReceiveChannel.objects.filter(pk=alert_receive_channel_id).first()
    if not alert_receive_channel:
        logger.debug(
            f"Create CP task: Cannot create contact point for integration {alert_receive_channel_id}: "
            f"integration does not exist"
        )
        return

    grafana_alerting_sync_manager = alert_receive_channel.grafana_alerting_sync_manager
    logger.debug(
        f"Create CP task: Create contact points for integration {alert_receive_channel_id}, "
        f"retry counter: {create_contact_points_for_datasource.request.retries}, datasource list {len(datasource_list)}"
    )
    # list of datasource for which contact point creation was failed
    datasources_to_create = []
    for datasource in datasource_list:
        datasource_type = datasource.get("type")
        logger.debug(
            f"Create CP task: Create contact point for datasource {datasource_type} "
            f"for integration {alert_receive_channel_id}"
        )
        contact_point, response_info = grafana_alerting_sync_manager.create_contact_point(datasource)

        if contact_point is None:
            if response_info.get("status_code") == status.HTTP_400_BAD_REQUEST:
                logger.warning(
                    f"Create CP task: Failed to create contact point for integration {alert_receive_channel_id}, "
                    f"datasource info: {datasource}; response: {response_info}. "
                    f"Got 400 Bad Request, exclude from retry list."
                )
                continue
            logger.warning(
                f"Create CP task: Failed to create contact point for integration {alert_receive_channel_id}, "
                f"datasource info: {datasource}; response: {response_info}. Retrying"
            )
            # Failed to create contact point. Add datasource to list and retry to create contact point for it again
            datasources_to_create.append(datasource)

    # if some contact points were not created, restart task for them
    if (
        datasources_to_create
        and create_contact_points_for_datasource.request.retries < create_contact_points_for_datasource.max_retries
    ):
        logger.debug(
            f"Create CP task: Retry to create contact points for integration {alert_receive_channel_id}, "
            f"retry counter: {create_contact_points_for_datasource.request.retries}, "
            f"datasource list {len(datasources_to_create)}"
        )
        # Save task id in cache and restart the task
        set_cache_key_create_contact_points_for_datasource(alert_receive_channel_id, current_task_id)
        create_contact_points_for_datasource.retry(args=(alert_receive_channel_id, datasources_to_create), countdown=3)
    else:
        alert_receive_channel.is_finished_alerting_setup = True
        alert_receive_channel.save(update_fields=["is_finished_alerting_setup"])
        logger.debug(
            f"Create CP task: Alerting setup for integration {alert_receive_channel_id} is finished, "
            f"retry counter: {create_contact_points_for_datasource.request.retries}, "
            f"datasource list {len(datasource_list)}"
        )
    logger.debug(
        f"Create CP task: Finished task to create contact points for integration {alert_receive_channel_id}, "
        f"datasource list {len(datasource_list)}"
    )
