import logging

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


MAX_RETRIES = 10


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_created(self, alert_group_id):
    logger.error("CREATED AG ID: %s", alert_group_id)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_status_change(self, action_type, alert_group_id, user_id):
    logger.error("TYPE: %s AG ID: %s USER ID: %s", action_type, alert_group_id, user_id)
