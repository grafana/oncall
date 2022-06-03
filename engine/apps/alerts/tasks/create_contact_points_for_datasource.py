from django.apps import apps
from rest_framework import status

from apps.grafana_plugin.helpers import GrafanaAPIClient
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def create_contact_points_for_datasource(alert_receive_channel_id, datasource_list):
    """
    Try to create contact points for other datasource.
    Restart task for datasource, for which contact point was not created.
    """

    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

    alert_receive_channel = AlertReceiveChannel.objects.get(pk=alert_receive_channel_id)

    client = GrafanaAPIClient(
        api_url=alert_receive_channel.organization.grafana_url,
        api_token=alert_receive_channel.organization.api_token,
    )
    # list of datasource for which contact point creation was failed
    datasource_to_create = []
    for datasource in datasource_list:
        contact_point = None
        config, response_info = client.get_alerting_config(datasource["id"])
        if config is None:
            if response_info.get("status_code") == status.HTTP_404_NOT_FOUND:
                client.get_alertmanager_status_with_config(datasource["id"])
                contact_point = alert_receive_channel.grafana_alerting_sync_manager.create_contact_point(datasource)
        else:
            contact_point = alert_receive_channel.grafana_alerting_sync_manager.create_contact_point(datasource)
        if contact_point is None:
            # Failed to create contact point duo to getting wrong alerting config.
            # Add datasource to list and retry to create contact point for it again
            datasource_to_create.append(datasource)

    # if some contact points were not created, restart task for them
    if datasource_to_create:
        create_contact_points_for_datasource.apply_async((alert_receive_channel_id, datasource_to_create), countdown=5)
    else:
        alert_receive_channel.is_finished_alerting_setup = True
        alert_receive_channel.save(update_fields=["is_finished_alerting_setup"])
