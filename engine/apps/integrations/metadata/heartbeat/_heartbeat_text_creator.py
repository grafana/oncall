from dataclasses import dataclass
from urllib.parse import urljoin

from django.conf import settings


@dataclass
class IntegrationHeartBeatText:
    heartbeat_expired_title: str = "heartbeat_expired"
    heartbeat_expired_message: str = "heartbeat_expired"
    heartbeat_restored_title: str = "hearbeat_restored"
    heartbeat_restored_message: str = "heartbeat_restored"
    heartbeat_instruction_template: str = None


class HearBeatTextCreator:
    def __init__(self, integration_verbal):
        self.integration_verbal = integration_verbal.capitalize()

    def get_heartbeat_texts(self):
        return IntegrationHeartBeatText(
            heartbeat_expired_title=self._get_heartbeat_expired_title(),
            heartbeat_expired_message=self._get_heartbeat_expired_message(),
            heartbeat_restored_title=self._get_heartbeat_restored_title(),
            heartbeat_restored_message=self._get_heartbeat_restored_message(),
            heartbeat_instruction_template=self._get_heartbeat_instruction_template(),
        )

    def _get_heartbeat_expired_title(self):
        heartbeat_expired_title = f"{self.integration_verbal} heartbeat is missing"
        return heartbeat_expired_title

    def _get_heartbeat_expired_message(self):
        heartbeat_docs_url = urljoin(settings.DOCS_URL, "/#/integrations/heartbeat")
        heartbeat_expired_message = (
            f"Amixr was waiting for a heartbeat from {self.integration_verbal}. "
            f"Heartbeat is missing. That could happen because {self.integration_verbal} stopped or"
            f" there are connectivity issues between Amixr and {self.integration_verbal}. "
            f"Read more in Amixr docs: {heartbeat_docs_url}"
        )
        return heartbeat_expired_message

    def _get_heartbeat_restored_title(self):
        heartbeat_expired_title = f"{self.integration_verbal} heartbeat restored"
        return heartbeat_expired_title

    def _get_heartbeat_restored_message(self):
        heartbeat_expired_message = f"Amixr received a signal from {self.integration_verbal}. Heartbeat restored."
        return heartbeat_expired_message

    def _get_heartbeat_instruction_template(self):
        return f"heartbeat_instructions/{self.integration_verbal.lower()}.html"


class HearBeatTextCreatorForTitleGrouping(HearBeatTextCreator):
    """
    Some integrations (Grafana, AlertManager) have default grouping template based on title
    """

    def _get_heartbeat_expired_title(self):
        heartbeat_expired_title = "Amixr heartbeat"
        return heartbeat_expired_title

    def _get_heartbeat_restored_title(self):
        heartbeat_expired_title = "Amixr heartbeat"
        return heartbeat_expired_title
