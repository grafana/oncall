import copy
import logging
from typing import TYPE_CHECKING, Optional, Tuple

from rest_framework import status

from apps.grafana_plugin.helpers import GrafanaAPIClient

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.alerts.models import AlertReceiveChannel
    from apps.user_management.models import Organization


class GrafanaAlertingSyncManager:
    """
    Get or update Alertmanager contact points for INTEGRATION_GRAFANA_ALERTING.
    Supports Grafana Alertmanager and datasources with type 'alertmanager' and implementation 'mimir' or 'cortex'
    """

    GRAFANA_ALERTING_DATASOURCE = "grafana"
    ALERTING_DATASOURCE = "alertmanager"
    CLOUD_ALERTING_DATASOURCE_UID = "grafanacloud-ngalertmanager"

    def __init__(self, alert_receive_channel: "AlertReceiveChannel") -> None:
        self.alert_receive_channel = alert_receive_channel
        self.client = GrafanaAPIClient(
            api_url=self.alert_receive_channel.organization.grafana_url,
            api_token=self.alert_receive_channel.organization.api_token,
        )
        self.integration_url = self.alert_receive_channel.integration_url

    @classmethod
    def check_for_connection_errors(cls, organization: "Organization") -> Optional[str]:
        """Check if it possible to connect to alerting, otherwise return error message"""
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        recipient = cls.GRAFANA_ALERTING_DATASOURCE
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

        return None

    # Actions with Alerting contact points
    @classmethod
    def get_contact_points(cls, organization: "Organization") -> list:
        """Get names of all available contact points from alerting configs, sorted by datasource"""
        logger.info(f"GrafanaAlertingSyncManager: start get_contact_points for organization {organization.id}")
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        datasources = cls.get_datasources(client)
        contact_points_with_datasource = []
        for datasource in datasources:
            contact_points = cls.get_contact_points_for_datasource(client, datasource["uid"])
            if contact_points:
                contact_points_with_datasource.append(
                    {
                        "name": datasource.get("name"),
                        "uid": datasource.get("uid"),
                        "contact_points": contact_points,
                    }
                )
        return contact_points_with_datasource

    def get_connected_contact_points(self) -> list:
        """
        Get names and their active status (using in alerting notifications) of all contact points connected
        to selected OnCall integration from alerting configs, sorted by datasource
        """
        logger.info(
            f"GrafanaAlertingSyncManager: start get_connected_contact_points for integration "
            f"{self.alert_receive_channel.id} for organization {self.alert_receive_channel.organization.id}"
        )
        datasources = self.get_datasources(self.client)
        contact_points_with_datasource = []
        for datasource in datasources:
            connected_contact_points = self.get_connected_contact_points_for_datasource(datasource.get("uid"))
            if connected_contact_points:
                contact_points_with_datasource.append(
                    {
                        "name": datasource.get("name"),
                        "uid": datasource.get("uid"),
                        "contact_points": connected_contact_points,
                    }
                )
        return contact_points_with_datasource

    def connect_contact_point(
        self, datasource_uid: str, contact_point_name: str, create_new: bool = False
    ) -> Tuple[bool, str]:
        """
        Connect OnCall integration to selected contact point or create a new one if `create_new` is True
        """
        logger.info(
            f"GrafanaAlertingSyncManager: start connect_contact_point for integration {self.alert_receive_channel.id} "
            f"for organization {self.alert_receive_channel.organization.id}"
        )
        is_grafana_datasource = datasource_uid == self.GRAFANA_ALERTING_DATASOURCE
        config = self.get_alerting_config_for_datasource(self.client, datasource_uid)
        if config is None or config.get("alertmanager_config") is None:
            # Config was probably deleted. Grafana Alertmanager should return config in any case. Try to get default
            # config from another endpoint if it's not Grafana Alertmanager
            if is_grafana_datasource:
                return False, "Failed to get Alertmanager config"
            default_config = self.get_default_mimir_alertmanager_config_for_datasource(self.client, datasource_uid)
            if default_config is None:
                return False, "Failed to get Alertmanager config"
            updated_config = default_config
        else:
            updated_config = copy.deepcopy(config)

        alertmanager_config = updated_config.get("alertmanager_config")
        if not alertmanager_config:
            return False, "Failed to get Alertmanager config"
        alerting_receivers = alertmanager_config.get("receivers", [])

        is_oncall_type_available = self.check_if_oncall_type_is_available(is_grafana_datasource)

        oncall_config, config_field = self._get_oncall_config_and_config_field_for_datasource_type(
            contact_point_name, is_grafana_datasource, is_oncall_type_available
        )
        if create_new:
            if contact_point_name in [receiver["name"] for receiver in alerting_receivers]:
                return False, "Contact point already exists"
            alerting_receivers.append({"name": contact_point_name, config_field: [oncall_config]})
        else:
            receiver_found = False
            for receiver in alerting_receivers:
                if receiver["name"] == contact_point_name:
                    receiver_found = True
                    receiver.setdefault(config_field, []).append(oncall_config)
                    break
            if not receiver_found:
                return False, "Contact point was not found"

        response = self.update_alerting_config_for_datasource(self.client, datasource_uid, config, updated_config)
        if response is None:
            return False, "Failed to update Alertmanager config"
        return True, ""

    def disconnect_contact_point(self, datasource_uid: str, contact_point_name: str) -> Tuple[bool, str]:
        """
        Disconnect OnCall integration from selected contact point
        """
        logger.info(
            f"GrafanaAlertingSyncManager: start disconnect_contact_point for integration "
            f"{self.alert_receive_channel.id} for organization {self.alert_receive_channel.organization.id}"
        )
        is_grafana_datasource = datasource_uid == self.GRAFANA_ALERTING_DATASOURCE
        config = self.get_alerting_config_for_datasource(self.client, datasource_uid)
        if config is None:
            return False, "Failed to get Alertmanager config"
        updated_config = copy.deepcopy(config)
        alertmanager_config = updated_config.get("alertmanager_config")
        if not alertmanager_config:
            return False, "Failed to get Alertmanager config"
        _, contact_point_found, receiver_found = self._remove_oncall_config_from_contact_point(
            contact_point_name, is_grafana_datasource, alertmanager_config
        )
        if not contact_point_found:
            return False, "Contact point was not found"
        elif not receiver_found:
            return False, "OnCall connection was not found in selected contact point"
        response = self.update_alerting_config_for_datasource(self.client, datasource_uid, config, updated_config)
        if response is None:
            return False, "Failed to update Alertmanager config"
        return True, ""

    def disconnect_all_contact_points(self) -> None:
        """
        Disconnect OnCall integration from all contact points (used for deleted OnCall integrations)
        """
        logger.info(
            f"GrafanaAlertingSyncManager: start disconnect_all_contact_points for integration "
            f"{self.alert_receive_channel.id} for organization {self.alert_receive_channel.organization.id}"
        )
        datasources = self.get_datasources(self.client)
        for datasource in datasources:
            datasource_uid = datasource["uid"]
            is_grafana_datasource = datasource_uid == self.GRAFANA_ALERTING_DATASOURCE
            config = self.get_alerting_config_for_datasource(self.client, datasource_uid)
            if config is None:
                continue
            updated_config = copy.deepcopy(config)
            alertmanager_config = updated_config.get("alertmanager_config")
            if not alertmanager_config:
                continue
            self._remove_integration_config_from_each_contact_point(is_grafana_datasource, alertmanager_config)
            self.update_alerting_config_for_datasource(self.client, datasource_uid, config, updated_config)
        return

    # API requests to get/update Alertmanager config
    @classmethod
    def get_alerting_config_for_datasource(cls, client: "GrafanaAPIClient", datasource_uid: str) -> Optional[dict]:
        config, response_info = client.get_alerting_config(datasource_uid)
        if config is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Got config None in get_alerting_config_for_datasource "
                f"for is_grafana_datasource {datasource_uid == cls.GRAFANA_ALERTING_DATASOURCE}, "
                f"response: {response_info}"
            )
            return
        return config

    @classmethod
    def get_default_mimir_alertmanager_config_for_datasource(
        cls, client: "GrafanaAPIClient", datasource_uid: str
    ) -> Optional[dict]:
        # Get default config for Mimir/Cortex Alertmanager
        default_config, response_info = client.get_alertmanager_status_with_config(datasource_uid)
        if default_config is None or not default_config.get("config"):
            logger.warning(
                f"GrafanaAlertingSyncManager: Got default config None in get_alerting_config_for_datasource "
                f"for is_grafana_datasource False; response: {response_info}"
            )
            return
        default_config = {"alertmanager_config": copy.deepcopy(default_config["config"])}
        return default_config

    @classmethod
    def update_alerting_config_for_datasource(
        cls, client: "GrafanaAPIClient", datasource_uid: str, config: dict, updated_config: dict
    ) -> Optional[dict]:
        response, response_info = client.update_alerting_config(datasource_uid, updated_config)
        if response is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to update contact point (POST) for is_grafana_datasource "
                f"{datasource_uid == cls.GRAFANA_ALERTING_DATASOURCE}; response: {response_info}"
            )
            if response_info.get("status_code") == status.HTTP_400_BAD_REQUEST:
                logger.warning(f"GrafanaAlertingSyncManager: Config: {config}, Updated config: {updated_config}")
        if response_info["status_code"] not in (
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED,
        ):
            return
        return response

    @classmethod
    def get_datasources(cls, client: "GrafanaAPIClient") -> list[dict]:
        alerting_datasources = []

        # Add Grafana Alerting Alertmanager
        grafana_alerting_datasource = {
            "uid": cls.GRAFANA_ALERTING_DATASOURCE,
            "name": "Grafana",
        }
        alerting_datasources.append(grafana_alerting_datasource)

        datasources, response_info = client.get_datasources()
        if datasources is None:
            logger.warning(
                f"GrafanaAlertingSyncManager: Failed to get datasource list for organization, {response_info}"
            )
            return alerting_datasources

        for datasource in datasources:
            # Get only Alertmanager datasources
            if datasource["type"] == cls.ALERTING_DATASOURCE:
                # Check datasource implementation in "jsonData" field. Only "cortex" and "mimir" implementations have
                # editable config. Also check if it is preinstalled Alertmanager on cloud since it is editable, but has
                # empty "jsonData" (probably will be fixed by Alerting)
                if (
                    datasource.get("jsonData", {}).get("implementation") in ["mimir", "cortex"]
                    or datasource.get("uid") == cls.CLOUD_ALERTING_DATASOURCE_UID
                ):
                    datasource_data = {
                        "uid": datasource["uid"],
                        "name": datasource["name"],
                    }
                    alerting_datasources.append(datasource_data)
        return alerting_datasources

    @classmethod
    def get_contact_points_for_datasource(cls, client: "GrafanaAPIClient", datasource_uid: str) -> Optional[list]:
        is_grafana_datasource = datasource_uid == cls.GRAFANA_ALERTING_DATASOURCE
        config = cls.get_alerting_config_for_datasource(client, datasource_uid)
        if config is None or config.get("alertmanager_config") is None:
            # Config was probably deleted. Grafana Alertmanager should return config in any case. Try to get default
            # config from another endpoint if it's not Grafana Alertmanager
            if not is_grafana_datasource:
                config = cls.get_default_mimir_alertmanager_config_for_datasource(client, datasource_uid)
            if is_grafana_datasource or config is None:
                return
        alertmanager_config = config.get("alertmanager_config")
        if not alertmanager_config:
            return
        alerting_receivers = alertmanager_config.get("receivers", [])
        contact_points = [receiver["name"] for receiver in alerting_receivers]
        return contact_points

    def get_connected_contact_points_for_datasource(self, datasource_uid: str) -> list:
        is_grafana_datasource = datasource_uid == self.GRAFANA_ALERTING_DATASOURCE
        config = self.get_alerting_config_for_datasource(self.client, datasource_uid)
        if config is None:
            return []
        alertmanager_config = config.get("alertmanager_config")
        if not alertmanager_config:
            return []
        contact_points = self._get_connected_contact_points_from_config(alertmanager_config, is_grafana_datasource)
        return contact_points

    def check_if_oncall_type_is_available(self, is_grafana_datasource: bool) -> bool:
        """
        `oncall` type is a new contact point type. Check if it is available in the current version of Grafana.
        If it's not - use `webhook` contact point type instead.
        """
        if is_grafana_datasource:
            response, response_info = self.client.get_alerting_notifiers()
            if response:
                receiver_types = [receiver_type["type"] for receiver_type in response]
                if "oncall" in receiver_types:
                    return True
        # todo: update for mimir when support for "oncall" receiver is added
        return False

    # Parsing Alertmanager config
    def _get_connected_contact_points_from_config(self, alertmanager_config: dict, is_grafana_datasource: bool) -> list:
        contact_points = []
        alerting_receivers = alertmanager_config.get("receivers", [])
        route_config = alertmanager_config.get("route", {})

        # parse Alertmanager config
        if is_grafana_datasource:  # Grafana Alertmanager
            for receiver in alerting_receivers:
                for receiver_config in receiver.get("grafana_managed_receiver_configs", []):
                    if (
                        receiver_config["type"] in ["webhook", "oncall"]
                        and receiver_config["settings"]["url"] == self.integration_url
                    ):
                        receiver_name = receiver["name"]
                        contact_points.append(
                            {
                                "name": receiver_name,
                                "notification_connected": self._recursive_check_contact_point_is_in_routes(
                                    route_config, receiver_name
                                ),
                            }
                        )
                        break
        else:  # other Alertmanagers
            for receiver in alerting_receivers:
                config_types = ["webhook_configs", "oncall_configs"]
                contact_point_connected = False
                for config_type in config_types:
                    if contact_point_connected:
                        break
                    for receiver_config in receiver.get(config_type, []):
                        if receiver_config["url"] == self.integration_url:
                            receiver_name = receiver["name"]

                            contact_points.append(
                                {
                                    "name": receiver_name,
                                    "notification_connected": self._recursive_check_contact_point_is_in_routes(
                                        route_config, receiver_name
                                    ),
                                }
                            )
                            contact_point_connected = True
                            break
        return contact_points

    def _recursive_check_contact_point_is_in_routes(self, route_config: dict, receiver_name: str) -> bool:
        if route_config.get("receiver") == receiver_name:
            return True
        routes = route_config.get("routes", [])
        for route in routes:
            if route.get("receiver") == receiver_name:
                return True
            if route.get("routes"):
                if self._recursive_check_contact_point_is_in_routes(route, receiver_name):
                    return True
        return False

    def _get_oncall_config_and_config_field_for_datasource_type(
        self, contact_point_name: str, is_grafana_datasource: bool, is_oncall_type_available: bool
    ) -> Tuple[dict, str]:
        if is_grafana_datasource:  # Grafana Alertmanager
            receiver_type = "oncall" if is_oncall_type_available else "webhook"
            oncall_config = {
                "name": contact_point_name,
                "type": receiver_type,
                "disableResolveMessage": False,
                "settings": {
                    "httpMethod": "POST",
                    "url": self.integration_url,
                },
                "secureFields": {},
            }
            config_field = "grafana_managed_receiver_configs"
        else:  # mimir/cortex Alertmanagers
            oncall_config = {
                "url": self.integration_url,
                "send_resolved": True,
            }
            config_field = "oncall_configs" if is_oncall_type_available else "webhook_configs"
        return oncall_config, config_field

    def _remove_oncall_config_from_contact_point(
        self, contact_point_name: str, is_grafana_datasource: bool, alertmanager_config: dict
    ) -> Tuple[dict, bool, bool]:
        """Remove OnCall integration config from selected contact point"""
        alerting_receivers = alertmanager_config.get("receivers", [])
        contact_point_found = False
        receiver_found = False
        if is_grafana_datasource:
            for receiver in alerting_receivers:
                if receiver["name"] == contact_point_name:
                    receiver_configs = receiver.get("grafana_managed_receiver_configs")
                    if not receiver_configs:
                        break
                    updated_receiver_configs = []
                    for receiver_config in receiver_configs:
                        if not (
                            receiver_config["type"] in ["webhook", "oncall"]
                            and receiver_config.get("settings", {}).get("url") == self.integration_url
                        ):
                            updated_receiver_configs.append(receiver_config)
                        else:
                            receiver_found = True
                    # update config only if receiver was found
                    if receiver_found:
                        receiver["grafana_managed_receiver_configs"] = updated_receiver_configs
                    contact_point_found = True
                elif contact_point_found:
                    break
        else:
            config_types = ["webhook_configs", "oncall_configs"]  # todo: check oncall_configs after mimir updates
            for receiver in alerting_receivers:
                if receiver["name"] == contact_point_name:
                    for config_type in config_types:
                        receiver_configs = receiver.get(config_type)
                        if not receiver_configs:
                            continue
                        updated_receiver_configs = []
                        for receiver_config in receiver_configs:
                            if not receiver_config.get("url") == self.integration_url:
                                updated_receiver_configs.append(receiver_config)
                            else:
                                receiver_found = True
                        # update config only if receiver was found
                        if receiver_found:
                            if updated_receiver_configs:
                                receiver[config_type] = updated_receiver_configs
                            else:
                                del receiver[config_type]
                    contact_point_found = True
                elif contact_point_found:
                    break
        return alertmanager_config, contact_point_found, receiver_found

    def _remove_integration_config_from_each_contact_point(
        self, is_grafana_datasource: bool, alertmanager_config: dict
    ) -> dict:
        """Remove OnCall integration config from all contact points"""
        alerting_receivers = alertmanager_config.get("receivers", [])
        receiver_found = False
        if is_grafana_datasource:
            for receiver in alerting_receivers:
                receiver_configs = receiver.get("grafana_managed_receiver_configs")
                if not receiver_configs:
                    continue
                updated_receiver_configs = []
                for receiver_config in receiver_configs:
                    if not (
                        receiver_config["type"] in ["webhook", "oncall"]
                        and receiver_config.get("settings", {}).get("url") == self.integration_url
                    ):
                        updated_receiver_configs.append(receiver_config)
                    else:
                        receiver_found = True
                # update config only if receiver was found
                if receiver_found:
                    receiver["grafana_managed_receiver_configs"] = updated_receiver_configs
        else:
            config_types = ["webhook_configs", "oncall_configs"]  # todo: check oncall_configs after mimir updates
            for receiver in alerting_receivers:
                for config_type in config_types:
                    receiver_configs = receiver.get(config_type)
                    if not receiver_configs:
                        continue
                    updated_receiver_configs = []
                    for receiver_config in receiver_configs:
                        if not receiver_config.get("url") == self.integration_url:
                            updated_receiver_configs.append(receiver_config)
                        else:
                            receiver_found = True
                    # update config only if receiver was found
                    if receiver_found:
                        if updated_receiver_configs:
                            receiver[config_type] = updated_receiver_configs
                        else:
                            del receiver[config_type]
        return alertmanager_config
