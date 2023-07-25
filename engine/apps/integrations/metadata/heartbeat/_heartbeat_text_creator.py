from dataclasses import dataclass

from django.conf import settings

from common.api_helpers.utils import create_engine_url


@dataclass
class IntegrationHeartBeatText:
    heartbeat_expired_title: str = "heartbeat_expired"
    heartbeat_expired_message: str = "heartbeat_expired"
    heartbeat_restored_title: str = "heartbeat_restored"
    heartbeat_restored_message: str = "heartbeat_restored"


class HeartBeatTextCreator:
    def __init__(self, integration_verbal):
        self.integration_verbal = integration_verbal.capitalize()

    def get_heartbeat_texts(self):
        return IntegrationHeartBeatText(
            heartbeat_expired_title=self._get_heartbeat_expired_title(),
            heartbeat_expired_message=self._get_heartbeat_expired_message(),
            heartbeat_restored_title=self._get_heartbeat_restored_title(),
            heartbeat_restored_message=self._get_heartbeat_restored_message(),
        )

    def _get_heartbeat_expired_title(self):
        heartbeat_expired_title = f"{self.integration_verbal} heartbeat is missing"
        return heartbeat_expired_title

    def _get_heartbeat_expired_message(self):
        heartbeat_docs_url = create_engine_url("/#/integrations/heartbeat", override_base=settings.DOCS_URL)
        heartbeat_expired_message = (
            f"Grafana OnCall was waiting for a heartbeat from {self.integration_verbal} "
            f"and one was not received. This can happen when {self.integration_verbal} has stopped or "
            f"there are connectivity issues between Grafana OnCall and {self.integration_verbal}. "
            f"You can read more in the Grafana OnCall docs here: {heartbeat_docs_url}"
        )
        return heartbeat_expired_message

    def _get_heartbeat_restored_title(self):
        heartbeat_expired_title = f"{self.integration_verbal} heartbeat restored"
        return heartbeat_expired_title

    def _get_heartbeat_restored_message(self):
        heartbeat_expired_message = (
            f"Grafana OnCall received a signal from {self.integration_verbal}. Heartbeat has been restored."
        )
        return heartbeat_expired_message


class HeartBeatTextCreatorForTitleGrouping(HeartBeatTextCreator):
    """
    Some integrations (Grafana, AlertManager) have default grouping template based on title
    """

    def _get_heartbeat_expired_title(self):
        heartbeat_expired_title = "Grafana OnCall heartbeat"
        return heartbeat_expired_title

    def _get_heartbeat_restored_title(self):
        heartbeat_expired_title = "Grafana OnCall heartbeat"
        return heartbeat_expired_title
