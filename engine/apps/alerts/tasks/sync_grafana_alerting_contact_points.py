from common.custom_celery_tasks import shared_dedicated_queue_retry_task


# deprecated
@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def sync_grafana_alerting_contact_points(alert_receive_channel_id):
    pass


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def disconnect_integration_from_alerting_contact_points(alert_receive_channel_id):
    from apps.alerts.models import AlertReceiveChannel

    alert_receive_channel = AlertReceiveChannel.objects_with_deleted.get(pk=alert_receive_channel_id)
    alert_receive_channel.grafana_alerting_sync_manager.disconnect_all_contact_points()
