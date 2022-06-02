import copy
import logging
from typing import Optional

from django.apps import apps
from rest_framework import status

from apps.alerts.tasks import create_contact_points_for_datasource
from apps.grafana_plugin.helpers import GrafanaAPIClient

logger = logging.getLogger(__name__)


class GrafanaAlertingSyncManager:
    """
    Create or update Grafana Alerting contact points and notification policies for INTEGRATION_GRAFANA_ALERTING
    by updating Grafana Alerting config for each datasource with type 'alertmanager'
    """

    GRAFANA_CONTACT_POINT = "grafana"
    ALERTING_DATASOURCE = "alertmanager"

    def __init__(self, alert_receive_channel):
        self.alert_receive_channel = alert_receive_channel
        self.client = GrafanaAPIClient(
            api_url=self.alert_receive_channel.organization.grafana_url,
            api_token=self.alert_receive_channel.organization.api_token,
        )

    @classmethod
    def check_for_connection_errors(cls, organization) -> Optional[str]:
        """Check if it possible to connect to alerting, otherwise return error message"""
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        recipient = cls.GRAFANA_CONTACT_POINT
        config, response_info = client.get_alerting_config(recipient)
        if config is None:
            logger.warning(
                f"Failed to connect to contact point (GET): Is unified alerting enabled on instance? {response_info}"
            )
            return (
                "Failed to create the integration with current Grafana Alerting. "
                "Please reach out to our support team"
            )

        datasource_list, response_info = client.get_datasources()
        if datasource_list is None:
            logger.warning(
                f"Failed to connect to alerting datasource (GET): Is unified alerting enabled "
                f"on instance? {response_info}"
            )
            return (
                "Failed to create the integration with current Grafana Alerting. "
                "Please reach out to our support team"
            )
        return

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
                f"Failed to get datasource list for organization {self.alert_receive_channel.organization.org_title}, "
                f"{response_info}"
            )
            return

        # list of datasource for which contact point creation was failed
        datasources_to_create = []
        # sync other datasource
        for datasource in datasources:
            if datasource["type"] == GrafanaAlertingSyncManager.ALERTING_DATASOURCE:
                if self.create_contact_point(datasource) is None:
                    # Failed to create contact point duo to getting wrong alerting config. It is expected behaviour.
                    # Add datasource to list and retry to create contact point for it async
                    datasources_to_create.append(datasource)

        if datasources_to_create:
            # create other contact points async
            create_contact_points_for_datasource.apply_async(
                (self.alert_receive_channel.pk, datasources_to_create),
            )
        else:
            self.alert_receive_channel.is_finished_alerting_setup = True
            self.alert_receive_channel.save(update_fields=["is_finished_alerting_setup"])

    def create_contact_point(self, datasource=None) -> Optional["apps.alerts.models.GrafanaAlertingContactPoint"]:
        """
        Try to create a contact point for datasource.
        Return None if contact point was not created otherwise return contact point object
        """
        if datasource is None:
            datasource = {}

        datasource_id_or_grafana = datasource.get("id") or GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
        datasource_type = datasource.get("type") or GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
        is_grafana_datasource = datasource.get("id") is None
        logger.info(
            f"Create contact point for {datasource_type} datasource, integration {self.alert_receive_channel.pk}"
        )
        config, response_info = self.client.get_alerting_config(datasource_id_or_grafana)

        if config is None:
            logger.warning(
                f"Failed to create contact point (GET) for integration {self.alert_receive_channel.pk}: "
                f"Is unified alerting enabled on instance? {response_info}"
            )
            return

        updated_config = copy.deepcopy(config)

        if config["alertmanager_config"] is None:
            default_config, response_info = self.client.get_alertmanager_status_with_config(datasource_id_or_grafana)
            if default_config is None:
                logger.warning(
                    f"Failed to create contact point (alertmanager_config is None) for integration "
                    f"{self.alert_receive_channel.pk}, {response_info}"
                )
                return
            updated_config = {"alertmanager_config": copy.deepcopy(default_config["config"])}

        receiver_name = self.alert_receive_channel.emojized_verbal_name

        routes = updated_config["alertmanager_config"]["route"].get("routes", [])
        new_route = GrafanaAlertingSyncManager._get_continue_route_config_for_datasource(
            is_grafana_datasource,
            receiver_name,
        )
        # Append the new route to the beginning of the list
        # It must have `continue=True` parameter otherwise it will intercept all the alerts
        updated_config["alertmanager_config"]["route"]["routes"] = [new_route] + routes

        receivers = updated_config["alertmanager_config"]["receivers"]
        new_receiver = GrafanaAlertingSyncManager._get_receiver_config_for_datasource(
            is_grafana_datasource,
            receiver_name,
            self.alert_receive_channel.integration_url,
        )
        updated_config["alertmanager_config"]["receivers"] = receivers + [new_receiver]

        response, response_info = self.client.update_alerting_config(updated_config, datasource_id_or_grafana)
        if response is None:
            logger.warning(
                f"Failed to create contact point for integration {self.alert_receive_channel.pk} (POST): {response_info}"
            )
            if response_info.get("status_code") == status.HTTP_400_BAD_REQUEST:
                logger.warning(f"Config: {config}\nUpdated config: {updated_config}")
            return

        config, response_info = self.client.get_alerting_config(datasource_id_or_grafana)
        contact_point = self._create_contact_point_from_payload(config, receiver_name, datasource)
        contact_point_created_text = "created" if contact_point else "not created, creation will be retried"
        logger.info(
            f"Finished creating contact point for {datasource_type} datasource, "
            f"integration {self.alert_receive_channel.pk}, contact point was {contact_point_created_text}"
        )
        return contact_point

    @staticmethod
    def _get_continue_route_config_for_datasource(is_grafana_datasource, receiver_name) -> dict:
        """Return route config, related on type of datasource"""

        if is_grafana_datasource:
            route = {
                "receiver": receiver_name,
                "continue": True,
            }
        else:
            route = {
                "continue": True,
                "group_by": [],
                "matchers": [],
                "receiver": receiver_name,
                "routes": [],
            }
        return route

    @staticmethod
    def _get_receiver_config_for_datasource(is_grafana_datasource, receiver_name, webhook_url) -> dict:
        """Return receiver config, related on type of datasource"""

        if is_grafana_datasource:
            receiver = {
                "name": receiver_name,
                "grafana_managed_receiver_configs": [
                    {
                        "name": receiver_name,
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
                "name": receiver_name,
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
        receiver_name,
        datasource,
    ) -> "apps.alerts.models.GrafanaAlertingContactPoint":
        """Get receiver data from payload and create contact point"""

        is_grafana_datasource = datasource.get("id") is None

        receiver_config = self._get_receiver_config(receiver_name, is_grafana_datasource, payload)

        GrafanaAlertingContactPoint = apps.get_model("alerts", "GrafanaAlertingContactPoint")
        contact_point = GrafanaAlertingContactPoint(
            alert_receive_channel=self.alert_receive_channel,
            name=receiver_config["name"],
            uid=receiver_config.get("uid"),  # uid is None for non-Grafana datasource
            datasource_name=datasource.get("name") or GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT,
            datasource_id=datasource.get("id"),  # id is None for Grafana datasource
        )
        contact_point.save()
        return contact_point

    def _get_receiver_config(self, receiver_name, is_grafana_datasource, payload):
        receiver_config = {}
        receivers = payload["alertmanager_config"]["receivers"]
        alerting_receiver = GrafanaAlertingSyncManager._get_receiver_by_name(receiver_name, receivers)

        if is_grafana_datasource:  # means that datasource is Grafana
            for config in alerting_receiver["grafana_managed_receiver_configs"]:
                if config["name"] == receiver_name:
                    receiver_config = config
                    break
        else:  # other datasource
            for config in alerting_receiver.get("webhook_configs", []):
                if config["url"] == self.alert_receive_channel.integration_url:
                    receiver_config = alerting_receiver
                    break
        return receiver_config

    @staticmethod
    def _get_receiver_by_name(receiver_name, receivers):
        for alerting_receiver in receivers:
            if alerting_receiver["name"] == receiver_name:
                return alerting_receiver

    def sync_each_contact_point(self) -> None:
        """Sync all channels contact points"""
        logger.info(f"Starting to sync contact point for integration {self.alert_receive_channel.pk}")
        contact_points = self.alert_receive_channel.contact_points.all()
        for contact_point in contact_points:
            self.sync_contact_point(contact_point)

    def sync_contact_point(self, contact_point) -> None:
        """Update name of contact point and related routes or delete it if integration was deleted"""
        datasource_id = contact_point.datasource_id or GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT
        datasource_type = "grafana" if not contact_point.datasource_id else "nongrafana"
        logger.info(
            f"Sync contact point for {datasource_type} (name: {contact_point.datasource_name}) datasource, integration "
            f"{self.alert_receive_channel.pk}"
        )

        config, response_info = self.client.get_alerting_config(datasource_id)
        if config is None:
            logger.warning(
                f"Failed to update contact point (GET) for integration {self.alert_receive_channel.pk}: Is unified "
                f"alerting enabled on instance? {response_info}"
            )
            return

        receivers = config["alertmanager_config"]["receivers"]
        name_in_alerting = self.find_name_of_contact_point(
            contact_point.uid,
            datasource_id,
            receivers,
        )

        updated_config = copy.deepcopy(config)
        # if integration exists, update name for contact point and related routes
        if self.alert_receive_channel.deleted_at is None:
            new_name = self.alert_receive_channel.emojized_verbal_name
            updated_config = GrafanaAlertingSyncManager._update_contact_point_name_in_config(
                updated_config,
                name_in_alerting,
                new_name,
            )
            contact_point.name = new_name
            if datasource_id != GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT:
                datasource_name = self.get_datasource_name(datasource_id)
                contact_point.datasource_name = datasource_name
            contact_point.save(update_fields=["name", "datasource_name"])
        # if integration was deleted, delete contact point and related routes
        else:
            updated_config = GrafanaAlertingSyncManager._remove_contact_point_from_config(
                updated_config,
                name_in_alerting,
            )

        response, response_info = self.client.update_alerting_config(updated_config, datasource_id)
        if response is None:
            logger.warning(
                f"Failed to update contact point for integration {self.alert_receive_channel.pk} "
                f"(POST): {response_info}"
            )
            return

        if self.alert_receive_channel.deleted_at:
            contact_point.delete()

        logger.info(
            f"Finish to sync contact point for {datasource_type} (name: {contact_point.datasource_name}) datasource, "
            f"integration {self.alert_receive_channel.pk}"
        )

    @classmethod
    def _update_contact_point_name_in_config(cls, config, name_in_alerting, new_name) -> dict:
        receivers = config["alertmanager_config"]["receivers"]
        route = config["alertmanager_config"]["route"]

        config["alertmanager_config"]["route"] = cls._recursive_rename_routes(route, name_in_alerting, new_name)

        for receiver in receivers:
            if receiver["name"] == name_in_alerting:
                receiver["name"] = new_name
            receiver_configs = receiver.get("grafana_managed_receiver_configs", [])
            for receiver_config in receiver_configs:
                if receiver_config["name"] == name_in_alerting:
                    receiver_config["name"] = new_name
        return config

    @classmethod
    def _recursive_rename_routes(cls, alerting_route, name_in_alerting, new_name) -> dict:
        routes = alerting_route.get("routes", [])
        for route in routes:
            if route["receiver"] == name_in_alerting:
                route["receiver"] = new_name

        for idx, nested_route in enumerate(routes):
            if nested_route.get("routes"):
                alerting_route["routes"][idx] = cls._recursive_rename_routes(nested_route, name_in_alerting, new_name)

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

    def find_name_of_contact_point(self, contact_point_uid, datasource_id, receivers) -> str:
        if datasource_id == GrafanaAlertingSyncManager.GRAFANA_CONTACT_POINT:
            name_in_alerting = self._find_name_of_contact_point_by_uid(contact_point_uid, receivers)
        else:
            name_in_alerting = self._find_name_of_contact_point_by_integration_url(receivers)
        return name_in_alerting

    def _find_name_of_contact_point_by_uid(self, contact_point_uid, receivers) -> str:
        """Find name of contact point for grafana datasource"""
        name_in_alerting = None
        # find name of contact point in alerting config by contact point uid
        for receiver in receivers:
            receiver_configs = receiver["grafana_managed_receiver_configs"]
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

    def get_datasource_name(self, datasource_id) -> str:
        datasource, _ = self.client.get_datasource(datasource_id)
        return datasource["name"]
