from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from django.utils.functional import cached_property

from apps.webhooks.models import Webhook


@dataclass
class WebhookPresetMetadata:
    id: str
    name: str
    logo: str
    description: str
    controlled_fields: List[str]


class WebhookPreset(ABC):
    @cached_property
    def metadata(self) -> WebhookPresetMetadata:
        return self._metadata()

    @abstractmethod
    def _metadata(self) -> WebhookPresetMetadata:
        raise NotImplementedError

    @abstractmethod
    def override_parameters_before_save(self, webhook: Webhook):
        """Implement this to write parameters before the webhook is saved to the database"""
        pass

    @abstractmethod
    def override_parameters_at_runtime(self, webhook: Webhook):
        """Implement this to write parameters before the webhook is executed (These will not be persisted)"""
        pass
