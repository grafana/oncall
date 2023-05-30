import copy
import logging
from typing import Optional, Tuple

from django.apps import apps
from rest_framework import status

from apps.alerts.tasks import schedule_create_contact_points_for_datasource
from apps.grafana_plugin.helpers import GrafanaAPIClient

logger = logging.getLogger(__name__)


class GrafanaAlertingSyncManager:
    """
    Create or update Grafana Alerting contact points and notification policies for INTEGRATION_GRAFANA_ALERTING
    by updating Grafana Alerting config for each datasource with type 'alertmanager'
    """

    GRAFANA_CONTACT_POINT = "grafana"
    ALERTING_DATASOURCE = "alertmanager"
    IS_GRAFANA_VERSION_GRE_9 = None

    def __init__(self, alert_receive_channel):
        self.alert_receive_channel = alert_receive_channel
        self.client = GrafanaAPIClient(
            api_url=self.alert_receive_channel.organization.grafana_url,
            api_token=self.alert_receive_channel.organization.api_token,
        )
        self.receiver_name = self.alert_receive_channel.emojized_verbal_name

    @classmethod
    def check_for_connection_errors(cls, organization) -> Optional[str]:
        """Check if it possible to connect to alerting, otherwise return error message"""
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        recipient = cls.GRAFANA_CONTACT_POINT
        config, response_info = client.get_alerting_config(recipient)
        if config is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to connect to contact point (GET): Is unified alerting enabled "
                f"on instance? {response_info}"
            )
            return (
                "Failed to create the integration with current Grafana Alerting. "
                "Please reach out to our support team"
            )

        datasource_list, response_info = client.get_datasources()
        if datasource_list is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to connect to alerting datasource (GET): "
                f"Is unified alerting enabled on instance? {response_info}"
            )
            return (
                "Failed to create the integration with current Grafana Alerting. "
                "Please reach out to our support team"
            )
        return

    def alerting_config_with_respect_to_grafana_version(
        self, is_grafana_datasource, datasource_id, datasource_uid, client_method, *args
    ):
        """Quick fix for deprecated grafana alerting api endpoints"""

        if is_grafana_datasource:
            datasource_attr = GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
            config, response_info = client_method(datasource_attr, *args)
        elif self.IS_GRAFANA_VERSION_GRE_9:
            # Get config by datasource uid for Grafana version >= 9
            datasource_attr = datasource_uid
            config, response_info = client_method(datasource_attr, *args)
        else:
            # Get config by datasource id for Grafana version < 9
            datasource_attr = datasource_id
            config, response_info = client_method(datasource_attr, *args)

            if response_info["status_code"] in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND):
                # Get config by datasource uid for Grafana version >= 9
                datasource_attr = datasource_uid
                config, response_info = client_method(datasource_attr, *args)
                if response_info["status_code"] in (
                    status.HTTP_200_OK,
                    status.HTTP_201_CREATED,
                    status.HTTP_202_ACCEPTED,
                    status.HTTP_204_NO_CONTENT,
                ):
                    self.IS_GRAFANA_VERSION_GRE_9 = True
        if config is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Got config None in alerting_config_with_respect_to_grafana_version "
                f"with method {client_method.__name__} for is_grafana_datasource {is_grafana_datasource} "
                f"for integration {self.alert_receive_channel.pk}; response: {response_info}"
            )
        return config, response_info

    def create_contact_points(self) -> None:
        """
        Get all alertmanager datasources and try to create contact points for them.
        Start async task to create contact points that was not created.
        If all contact points was created, set channel flag 'is_finished_alerting_setup' to True.
        """
        # create contact point for grafana alertmanager
        # in this case we don't have datasource data
        self.create_contact_point()
        # try to create other contact points
        datasources, response_info = self.client.get_datasources()
        if datasources is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to get datasource list for organization "
                f"{self.alert_receive_channel.organization.stack_slug} "
                f"for integration {self.alert_receive_channel.pk}, {response_info}"
            )
            return

        # list of datasource for which contact point creation was failed
        datasources_to_create = []
        # sync other datasource
        for datasource in datasources:
            if datasource["type"] == GrafanaAlertingSyncManager.ALERTING_DATASOURCE:
                contact_point, _ = self.create_contact_point(datasource)
                if contact_point is None:
                    # Failed to create contact point duo to getting wrong alerting config. It is expected behaviour.
                    # Add datasource to list and retry to create contact point for it async
                    datasources_to_create.append(datasource)

        if datasources_to_create:
            logger.warning(
                f"GrafanaAlertingSyncManager: Some contact points were not created for integration "
                f"{self.alert_receive_channel.pk}, trying to create async"
            )
            # create other contact points async
            schedule_create_contact_points_for_datasource(self.alert_receive_channel.pk, datasources_to_create)
        else:
            self.alert_receive_channel.is_finished_alerting_setup = True
            self.alert_receive_channel.save(update_fields=["is_finished_alerting_setup"])

    def create_contact_point(
        self, datasource=None
    ) -> Tuple[Optional["apps.alerts.models.GrafanaAlertingContactPoint"], dict]:
        """
        Update datasource config in Grafana Alerting and create OnCall contact point
        """
        if datasource is None:  # Means that we create contact point for default datasource
            datasource = {
                "type": GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT,
            }

        is_grafana_datasource = datasource.get("id") is None

        # get alerting config
        config, response_info, config_to_update = self.get_alerting_config_for_datasource(
            datasource, is_grafana_datasource
        )
        if not config_to_update:  # failed to get alerting config for this datasource
            return None, response_info

        updated_config_from_alerting, response_info = self.add_contact_point_to_grafana_alerting(
            datasource, is_grafana_datasource, config, config_to_update
        )

        if not updated_config_from_alerting:
            return None, response_info

        contact_point = self._create_contact_point_from_payload(updated_config_from_alerting, datasource)
        logger.info(
            f"GrafanaAlertingSyncManager: Contact point was created for datasource {datasource.get('type')} "
            f"for integration {self.alert_receive_channel.pk}."
        )
        return contact_point, response_info

    def get_alerting_config_for_datasource(
        self, datasource, is_grafana_datasource
    ) -> Tuple[Optional[dict], dict, Optional[dict]]:
        """
        Get datasource config from Grafana Alerting. If it doesn't exist, get default config for this datasource
        """

        grafana_version = ">= 9" if self.IS_GRAFANA_VERSION_GRE_9 else "< 9 or unknown"
        datasource_type = datasource.get("type")
        logger.info(
            f"GrafanaAlertingSyncManager: Get config for datasource {datasource_type} to create contact point "
            f"for integration {self.alert_receive_channel.pk}, Grafana version is {grafana_version}"
        )
        config, response_info = self.alerting_config_with_respect_to_grafana_version(
            is_grafana_datasource, datasource.get("id"), datasource.get("uid"), self.client.get_alerting_config
        )

        if config is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Got config None for datasource {datasource_type} "
                f"for integration {self.alert_receive_channel.pk} (GET). "
                f"Response: {response_info}. Is unified alerting enabled on instance? Trying to get default config. "
            )

        config_to_update = copy.deepcopy(config)

        if config is None or config.get("alertmanager_config") is None:
            default_config, response_info = self.alerting_config_with_respect_to_grafana_version(
                is_grafana_datasource,
                datasource.get("id"),
                datasource.get("uid"),
                self.client.get_alertmanager_status_with_config,
            )
            if default_config is None:
                logger.warning(
                    f"GrafanaAlertingSyncManager: Got default config None (alertmanager_config is None) "
                    f"for datasource {datasource_type}. "
                    f"Failed to create contact point for integration {self.alert_receive_channel.pk}. "
                    f"Response: {response_info}"
                )
                return config, response_info, None

            config_to_update = {"alertmanager_config": copy.deepcopy(default_config["config"])}
        logger.debug(
            f"GrafanaAlertingSyncManager: Successfully got config for datasource {datasource_type} "
            f"for integration {self.alert_receive_channel.pk}."
        )
        return config, response_info, config_to_update

    def add_contact_point_to_grafana_alerting(
        self, datasource, is_grafana_datasource, config, config_to_update
    ) -> Tuple[Optional[dict], dict]:
        """
        Update datasource config with OnCall route and receiver and POST updated config to Grafana Alerting
        """
        updated_config = self._add_contact_point_to_config(is_grafana_datasource, config_to_update)
        updated_config_from_alerting, response_info = self.post_updated_config_and_get_the_result(
            datasource,
            is_grafana_datasource,
            config,
            updated_config,
        )
        return updated_config_from_alerting, response_info

    def post_updated_config_and_get_the_result(
        self,
        datasource,
        is_grafana_datasource,
        config,
        updated_config,
    ) -> Tuple[Optional[dict], Optional[dict]]:
        """
        POST updated datasource config to Grafana Alerting and GET the new alerting config
        """
        datasource_type = datasource.get("type")
        logger.info(
            f"GrafanaAlertingSyncManager: Post updated config for datasource {datasource_type} to create contact point "
            f"for integration {self.alert_receive_channel.pk}"
        )
        response, response_info = self.alerting_config_with_respect_to_grafana_version(
            is_grafana_datasource,
            datasource.get("id"),
            datasource.get("uid"),
            self.client.update_alerting_config,
            updated_config,
        )
        if response is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to create contact point for integration "
                f"{self.alert_receive_channel.pk} (POST). Response: {response_info}"
            )
            if response_info.get("status_code") == status.HTTP_400_BAD_REQUEST:
                logger.warning(f"GrafanaAlertingSyncManager: Config: {config}, Updated config: {updated_config}")
            return None, response_info

        logger.info(
            f"GrafanaAlertingSyncManager: Get updated config for datasource {datasource_type} to create contact point "
            f"for integration {self.alert_receive_channel.pk}"
        )
        new_config, response_info = self.alerting_config_with_respect_to_grafana_version(
            is_grafana_datasource, datasource.get("id"), datasource.get("uid"), self.client.get_alerting_config
        )
        if new_config:
            logger.info(
                f"GrafanaAlertingSyncManager: Alerting config for {datasource_type} datasource was successfully "
                f"updated with contact point for integration {self.alert_receive_channel.pk}"
            )
        else:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to get updated config to create contact point for integration "
                f"{self.alert_receive_channel.pk} (GET). Response: {response_info}"
            )
        return new_config, response_info

    def _add_contact_point_to_config(self, is_grafana_datasource, config_to_update) -> dict:
        routes = config_to_update["alertmanager_config"]["route"].get("routes", [])
        new_route = self._get_continue_route_config_for_datasource(
            is_grafana_datasource,
        )
        # Append the new route to the beginning of the list
        # It must have `continue=True` parameter otherwise it will intercept all the alerts
        config_to_update["alertmanager_config"]["route"]["routes"] = [new_route] + routes

        receivers = config_to_update["alertmanager_config"]["receivers"]
        new_receiver = self._get_receiver_config_for_datasource(
            is_grafana_datasource,
            self.alert_receive_channel.integration_url,
        )
        config_to_update["alertmanager_config"]["receivers"] = receivers + [new_receiver]
        return config_to_update

    def _get_continue_route_config_for_datasource(self, is_grafana_datasource) -> dict:
        """Return route config, related on type of datasource"""

        if is_grafana_datasource:
            route = {
                "receiver": self.receiver_name,
                "continue": True,
            }
        else:
            route = {
                "continue": True,
                "group_by": [],
                "matchers": [],
                "receiver": self.receiver_name,
                "routes": [],
            }
        return route

    def _get_receiver_config_for_datasource(self, is_grafana_datasource, webhook_url) -> dict:
        """Return receiver config, related on type of datasource"""

        if is_grafana_datasource:
            receiver = {
                "name": self.receiver_name,
                "grafana_managed_receiver_configs": [
                    {
                        "name": self.receiver_name,
                        "type": "webhook",
                        "disableResolveMessage": False,
                        "settings": {
                            "httpMethod": "POST",
                            "url": webhook_url,
                        },
                        "secureFields": {},
                    }
                ],
            }
        else:
            receiver = {
                "name": self.receiver_name,
                "webhook_configs": [
                    {
                        "send_resolved": True,
                        "url": webhook_url,
                    }
                ],
            }
        return receiver

    def _create_contact_point_from_payload(
        self,
        payload,
        datasource,
    ) -> "apps.alerts.models.GrafanaAlertingContactPoint":
        """Get receiver data from payload and create contact point"""

        is_grafana_datasource = datasource.get("id") is None

        receiver_config = self._get_receiver_config(is_grafana_datasource, payload)

        GrafanaAlertingContactPoint = apps.get_model("alerts", "GrafanaAlertingContactPoint")
        contact_point = GrafanaAlertingContactPoint(
            alert_receive_channel=self.alert_receive_channel,
            name=receiver_config["name"],
            uid=receiver_config.get("uid"),  # uid is None for non-Grafana datasource
            datasource_name=datasource.get("name") or GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT,
            datasource_id=datasource.get("id"),  # id is None for Grafana datasource
            datasource_uid=datasource.get("uid"),  # uid is None for Grafana datasource
        )
        contact_point.save()
        return contact_point

    def _get_receiver_config(self, is_grafana_datasource, payload):
        receiver_config = {}
        receivers = payload["alertmanager_config"]["receivers"]
        alerting_receiver = self._get_receiver_by_name(receivers)

        if is_grafana_datasource:  # means that datasource is Grafana
            for config in alerting_receiver["grafana_managed_receiver_configs"]:
                if config["name"] == self.receiver_name:
                    receiver_config = config
                    break
        else:  # other datasource
            for config in alerting_receiver.get("webhook_configs", []):
                if config["url"] == self.alert_receive_channel.integration_url:
                    receiver_config = alerting_receiver
                    break
        return receiver_config

    def _get_receiver_by_name(self, receivers):
        for alerting_receiver in receivers:
            if alerting_receiver["name"] == self.receiver_name:
                return alerting_receiver

    def sync_each_contact_point(self) -> None:
        """Sync all channels contact points"""
        logger.info(
            f"GrafanaAlertingSyncManager: Starting to sync contact point for integration "
            f"{self.alert_receive_channel.pk}"
        )
        contact_points = self.alert_receive_channel.contact_points.all()
        for contact_point in contact_points:
            self.sync_contact_point(contact_point)

    def sync_contact_point(self, contact_point) -> None:
        """Update name of contact point and related routes or delete it if integration was deleted"""
        datasource_type = (
            GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
            if not (contact_point.datasource_id or contact_point.datasource_uid)
            else "nongrafana"
        )
        is_grafana_datasource = datasource_type == GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
        logger.info(
            f"GrafanaAlertingSyncManager: Sync contact point for {datasource_type} "
            f"(name: {contact_point.datasource_name}) datasource, for integration {self.alert_receive_channel.pk}"
        )

        config, response_info = self.alerting_config_with_respect_to_grafana_version(
            is_grafana_datasource,
            contact_point.datasource_id,
            contact_point.datasource_uid,
            self.client.get_alerting_config,
        )
        if config is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Got config None for datasource {datasource_type}. "
                f"Failed to update contact point for integration {self.alert_receive_channel.pk} (GET). "
                f"Response: {response_info}. Is unified alerting enabled on instance? "
            )
            return

        receivers = config["alertmanager_config"]["receivers"]
        name_in_alerting = self.find_name_of_contact_point(
            contact_point.uid,
            is_grafana_datasource,
            receivers,
        )
        updated_config = copy.deepcopy(config)
        # if integration exists, update name for contact point and related routes
        if self.alert_receive_channel.deleted_at is None:
            updated_config = self._update_contact_point_name_in_config(
                updated_config,
                name_in_alerting,
            )
            contact_point.name = self.receiver_name
            if not is_grafana_datasource:
                datasource_name = self.get_datasource_name(contact_point)
                contact_point.datasource_name = datasource_name
            contact_point.save(update_fields=["name", "datasource_name"])
        # if integration was deleted, delete contact point and related routes
        else:
            updated_config = GrafanaAlertingSyncManager._remove_contact_point_from_config(
                updated_config,
                name_in_alerting,
            )
        response, response_info = self.alerting_config_with_respect_to_grafana_version(
            is_grafana_datasource,
            contact_point.datasource_id,
            contact_point.datasource_uid,
            self.client.update_alerting_config,
            updated_config,
        )
        if response is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to update contact point for integration "
                f"{self.alert_receive_channel.pk} (POST). Response: {response_info}"
            )
            if response_info.get("status_code") == status.HTTP_400_BAD_REQUEST:
                logger.warning(f"GrafanaAlertingSyncManager: Config: {config}, Updated config: {updated_config}")
            return

        if self.alert_receive_channel.deleted_at:
            contact_point.delete()

        logger.info(
            f"GrafanaAlertingSyncManager: Finish to sync contact point for {datasource_type} "
            f"(name: {contact_point.datasource_name}) datasource, integration {self.alert_receive_channel.pk}"
        )

    def _update_contact_point_name_in_config(self, config, name_in_alerting) -> dict:
        receivers = config["alertmanager_config"]["receivers"]
        route = config["alertmanager_config"]["route"]

        config["alertmanager_config"]["route"] = self._recursive_rename_routes(route, name_in_alerting)

        for receiver in receivers:
            if receiver["name"] == name_in_alerting:
                receiver["name"] = self.receiver_name
            receiver_configs = receiver.get("grafana_managed_receiver_configs", [])
            for receiver_config in receiver_configs:
                if receiver_config["name"] == name_in_alerting:
                    receiver_config["name"] = self.receiver_name
        return config

    def _recursive_rename_routes(self, alerting_route, name_in_alerting) -> dict:
        routes = alerting_route.get("routes", [])
        for route in routes:
            if route["receiver"] == name_in_alerting:
                route["receiver"] = self.receiver_name

        for idx, nested_route in enumerate(routes):
            if nested_route.get("routes"):
                alerting_route["routes"][idx] = self._recursive_rename_routes(nested_route, name_in_alerting)

        return alerting_route

    @classmethod
    def _remove_contact_point_from_config(cls, config, name_in_alerting) -> dict:
        receivers = config["alertmanager_config"]["receivers"]
        route = config["alertmanager_config"]["route"]

        config["alertmanager_config"]["route"] = cls._recursive_remove_routes(route, name_in_alerting)

        updated_receivers = [receiver for receiver in receivers if receiver["name"] != name_in_alerting]
        config["alertmanager_config"]["receivers"] = updated_receivers

        return config

    @classmethod
    def _recursive_remove_routes(cls, alerting_route, name_in_alerting) -> dict:
        routes = alerting_route.get("routes", [])
        alerting_route["routes"] = [route for route in routes if route["receiver"] != name_in_alerting]

        for idx, nested_route in enumerate(alerting_route["routes"]):
            if nested_route.get("routes"):
                alerting_route["routes"][idx] = cls._recursive_remove_routes(nested_route, name_in_alerting)

        return alerting_route

    def find_name_of_contact_point(self, contact_point_uid, is_grafana_datasource, receivers) -> str:
        if is_grafana_datasource:
            name_in_alerting = self._find_name_of_contact_point_by_uid(contact_point_uid, receivers)
        else:
            name_in_alerting = self._find_name_of_contact_point_by_integration_url(receivers)
        return name_in_alerting

    def _find_name_of_contact_point_by_uid(self, contact_point_uid, receivers) -> str:
        """Find name of contact point for grafana datasource"""
        name_in_alerting = None
        # find name of contact point in alerting config by contact point uid
        for receiver in receivers:
            receiver_configs = receiver.get("grafana_managed_receiver_configs", [])
            for receiver_config in receiver_configs:
                if receiver_config["uid"] == contact_point_uid:
                    name_in_alerting = receiver_config["name"]
                    break
            if name_in_alerting:
                break
        return name_in_alerting

    def _find_name_of_contact_point_by_integration_url(self, receivers) -> str:
        """Find name of contact point for nongrafana datasource"""
        name_in_alerting = None
        integration_url = self.alert_receive_channel.integration_url
        # find name of contact point in alerting config by contact point uid
        for receiver in receivers:
            webhook_configs = receiver.get("webhook_configs", [])
            for webhook_config in webhook_configs:
                if webhook_config["url"] == integration_url:
                    name_in_alerting = receiver["name"]
                    break
            if name_in_alerting:
                break
        return name_in_alerting

    def get_datasource_name(self, contact_point) -> str:
        datasource_id = contact_point.datasource_id
        datasource_uid = contact_point.datasource_uid
        datasource, response_info = self.client.get_datasource(datasource_uid)
        if response_info["status_code"] != 200:
            # For old Grafana versions (< 9) try to use deprecated endpoint
            datasource, _ = self.client.get_datasource_by_id(datasource_id)
        return datasource["name"]
