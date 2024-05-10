from abc import ABC, abstractmethod

from apps.slack.installation import install_slack_integration
from apps.user_management.models import Organization

from .types import INTEGRATION_INSTALLED_EVENT_TYPE, PROVIDER_TYPE_SLACK, Event, IntegrationInstalledData


class Handler(ABC):
    @classmethod
    @abstractmethod
    def match(cls, event: Event) -> bool:
        pass

    @classmethod
    @abstractmethod
    def handle(cls, event_data: dict) -> None:
        pass


class SlackInstallationHandler(Handler):
    @classmethod
    def match(cls, event: Event) -> bool:
        return (
            event.get("event_type") == INTEGRATION_INSTALLED_EVENT_TYPE
            and event.get("data").get("provider_type") == PROVIDER_TYPE_SLACK
        )

    @classmethod
    def handle(cls, data: IntegrationInstalledData) -> None:
        stack_id = data.get("stack_id")
        user_id = data.get("grafana_user_id")
        payload = data.get("payload")

        organization = Organization.objects.get(stack_id=stack_id)
        user = organization.users.get(user_id=user_id)
        install_slack_integration(organization, user, payload)
