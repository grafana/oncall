import logging
import typing
from abc import ABC, abstractmethod

from apps.chatops_proxy.client import PROVIDER_TYPE_SLACK
from apps.slack.installation import SlackInstallationExc, install_slack_integration, uninstall_slack_integration
from apps.user_management.models import Organization

from .types import (
    INTEGRATION_INSTALLED_EVENT_TYPE,
    INTEGRATION_UNINSTALLED_EVENT_TYPE,
    Event,
    IntegrationInstalledData,
    IntegrationUninstalledData,
)

logger = logging.getLogger(__name__)


class Handler(ABC):
    @classmethod
    @abstractmethod
    def match(cls, event: Event) -> bool:
        pass

    @classmethod
    @abstractmethod
    def handle(cls, event_data: dict) -> None:
        pass


class SlackInstallHandler(Handler):
    @classmethod
    def match(cls, event: Event) -> bool:
        return (
            event.get("event_type") == INTEGRATION_INSTALLED_EVENT_TYPE
            and event.get("data", {}).get("provider_type") == PROVIDER_TYPE_SLACK
        )

    @classmethod
    def handle(cls, data: dict) -> None:
        data = typing.cast(IntegrationInstalledData, data)

        stack_id = data.get("stack_id")
        user_id = data.get("grafana_user_id")
        payload = data.get("payload")

        organization = Organization.objects.get(stack_id=stack_id)
        user = organization.users.get(user_id=user_id)
        try:
            install_slack_integration(organization, user, payload)
        except SlackInstallationExc as e:
            logger.exception(
                f'msg="SlackInstallationHandler: Failed to install Slack integration: %s" org_id={organization.id} stack_id={stack_id}',
                e,
            )


class SlackUninstallHandler(Handler):
    @classmethod
    def match(cls, event: Event) -> bool:
        return (
            event.get("event_type") == INTEGRATION_UNINSTALLED_EVENT_TYPE
            and event.get("data", {}).get("provider_type") == PROVIDER_TYPE_SLACK
        )

    @classmethod
    def handle(cls, data: dict) -> None:
        data = typing.cast(IntegrationUninstalledData, data)

        stack_id = data.get("stack_id")
        user_id = data.get("grafana_user_id")

        organization = Organization.objects.get(stack_id=stack_id)
        user = organization.users.get(user_id=user_id)
        try:
            uninstall_slack_integration(organization, user)
        except SlackInstallationExc as e:
            logger.exception(
                f'msg="SlackInstallationHandler: Failed to uninstall Slack integration: %s" org_id={organization.id} stack_id={stack_id}',
                e,
            )
