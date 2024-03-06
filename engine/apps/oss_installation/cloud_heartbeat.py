import logging
import random
from urllib.parse import urljoin

import requests
from django.conf import settings
from rest_framework import status

from apps.base.utils import live_settings
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


def setup_heartbeat_integration(name=None):
    """Setup Grafana Cloud OnCall heartbeat integration."""
    from apps.oss_installation.models import CloudHeartbeat

    cloud_heartbeat = None
    api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
    if not live_settings.GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED or not api_token:
        return cloud_heartbeat
    # don't specify a team in the data, so heartbeat integration will be created in the General.
    name = name or f"OnCall Cloud Heartbeat {settings.BASE_URL}"
    data = {"type": "formatted_webhook", "name": name}
    url = create_engine_url("api/v1/integrations/", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)
    try:
        headers = {"Authorization": api_token}
        r = requests.post(url=url, data=data, headers=headers, timeout=5)
        if r.status_code == status.HTTP_201_CREATED:
            response_data = r.json()
            cloud_heartbeat, _ = CloudHeartbeat.objects.update_or_create(
                defaults={"integration_id": response_data["id"], "integration_url": response_data["heartbeat"]["link"]}
            )
        if r.status_code == status.HTTP_400_BAD_REQUEST:
            response_data = r.json()
            error = response_data["detail"]
            if error == "Integration with this name already exists":
                response = requests.get(url=f"{url}?name={name}", headers=headers)
                integrations = response.json().get("results", [])
                if len(integrations) == 1:
                    integration = integrations[0]
                    cloud_heartbeat, _ = CloudHeartbeat.objects.update_or_create(
                        defaults={
                            "integration_id": integration["id"],
                            "integration_url": integration["heartbeat"]["link"],
                        }
                    )
                else:
                    setup_heartbeat_integration(f"{name} { random.randint(1, 1024)}")
    except requests.Timeout:
        logger.warning("Unable to create cloud heartbeat integration. Request timeout.")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Unable to create cloud heartbeat integration. Request exception {str(e)}.")
    return cloud_heartbeat


def send_cloud_heartbeat():
    from apps.oss_installation.models import CloudConnector, CloudHeartbeat

    """Send heartbeat to Grafana Cloud OnCall integration."""
    if not live_settings.GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED or not live_settings.GRAFANA_CLOUD_ONCALL_TOKEN:
        logger.info(
            "Unable to send cloud heartbeat. Check values for GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED and GRAFANA_CLOUD_ONCALL_TOKEN."
        )
        return
    connector = CloudConnector.objects.first()
    if connector is None:
        logger.info("Unable to send cloud heartbeat. Cloud is not connected")
        return
    logger.info("Start send cloud heartbeat")
    try:
        cloud_heartbeat = CloudHeartbeat.objects.get()
    except CloudHeartbeat.DoesNotExist:
        cloud_heartbeat = setup_heartbeat_integration()

    if cloud_heartbeat is None:
        logger.warning("Unable to setup cloud heartbeat integration.")
        return
    cloud_heartbeat.success = False
    try:
        response = requests.get(cloud_heartbeat.integration_url, timeout=5)
        logger.info(f"Send cloud heartbeat with response {response.status_code}")
    except requests.Timeout:
        logger.warning("Unable to send cloud heartbeat. Request timeout.")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Unable to send cloud heartbeat. Request exception {str(e)}.")
    else:
        if response.status_code == status.HTTP_200_OK:
            cloud_heartbeat.success = True
            logger.info("Successfully send cloud heartbeat")
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            # check for 403 because AlertChannelDefiningMixin returns 403 if no integration was found.
            logger.info("Failed to send cloud heartbeat. Integration was not created yet")
            # force re-creation on next run
            cloud_heartbeat.delete()
        else:
            logger.info(f"Failed to send cloud heartbeat. response {response.status_code}")
    # save result of cloud heartbeat if it wasn't deleted
    if cloud_heartbeat.pk is not None:
        cloud_heartbeat.save()
    logger.info("Finish send cloud heartbeat")


def get_heartbeat_link(connector, heartbeat):
    if connector is None:
        return None
    if heartbeat is None:
        return None
    return urljoin(connector.cloud_url, f"a/grafana-oncall-app/?page=integrations&id={heartbeat.integration_id}")
