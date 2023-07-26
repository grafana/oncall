from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def sync_grafana_alerting_contact_points(alert_receive_channel_id):
    from apps.alerts.models import AlertReceiveChannel

    alert_receive_channel = AlertReceiveChannel.objects_with_deleted.get(pk=alert_receive_channel_id)

    GrafanaAlertingSyncManager(alert_receive_channel).sync_each_contact_point()
