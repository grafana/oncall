from celery.utils.log import get_task_logger
from django.utils import timezone

from apps.base.utils import live_settings
from apps.oss_installation.cloud_heartbeat import send_cloud_heartbeat
from apps.oss_installation.models import CloudConnector, OssInstallation
from apps.oss_installation.usage_stats import UsageStatsService
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def send_usage_stats_report():
    logger.info("Start send_usage_stats_report")
    installation = OssInstallation.objects.get_or_create()[0]
    enabled = live_settings.SEND_ANONYMOUS_USAGE_STATS
    if enabled:
        logger.info("send_usage_stats_report is enabled")
        service = UsageStatsService()
        service.send_usage_stats_report()
    else:
        logger.info("send_usage_stats_report is disabled")
    installation.report_sent_at = timezone.now()
    installation.save()
    logger.info("Finish send_usage_stats_report")


@shared_dedicated_queue_retry_task()
def send_cloud_heartbeat_task():
    send_cloud_heartbeat()


@shared_dedicated_queue_retry_task()
def sync_users_with_cloud():
    logger.info("Start sync_users_with_cloud")
    connector = CloudConnector.objects.first()
    if connector is not None:
        status, error = connector.sync_users_with_cloud()
        log_message = "Users synced. Status {status}."
        if error:
            log_message += f" Error {error}"
        logger.info(log_message)
    else:
        logger.info("Grafana Cloud is not connected")
