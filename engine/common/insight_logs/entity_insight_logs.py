import enum
import json
import logging
from abc import ABC, abstractmethod

from apps.user_management.models import User

insight_logger = logging.getLogger("insight_logger")

EVENT_CREATED = "created"
EVENT_UPDATED = "updated"
EVENT_DELETED = "removed"


class EntityEvent(enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class InsightLoggable(ABC):
    @property
    @abstractmethod
    def public_primary_key(self):
        pass

    @property
    @abstractmethod
    def insight_logs_verbal(self) -> str:
        pass

    @property
    @abstractmethod
    def insight_logs_type_verbal(self) -> str:
        pass

    @abstractmethod
    def format_insight_logs(self, diff) -> dict:
        pass

    @property
    @abstractmethod
    def insight_logs_dict(self) -> dict:
        pass


def entity_created_insight_logs(instance: InsightLoggable, user: User):
    _entity_insight_logs(instance, user, EntityEvent.CREATED)


def entity_updated_insight_logs(instance: InsightLoggable, user: User, before: dict, after: dict):
    before, after = _insight_diff_finder(before, after)
    before = json.dumps(instance.format_insight_logs(before))
    after = json.dumps(instance.format_insight_logs(after))
    _entity_insight_logs(instance, user, EntityEvent.UPDATED, before=before, after=after)


def entity_deleted_insight_logs(instance: InsightLoggable, user: User):
    _entity_insight_logs(instance, user, EntityEvent.DELETED)


def _entity_insight_logs(instance: InsightLoggable, user: User, event: EntityEvent, **kwargs):
    organization = user.organization
    tenant_id = organization.stack_id
    user_id = user.public_primary_key
    username = user.username
    entity_type = instance.insight_logs_type_verbal
    entity_id = instance.public_primary_key or instance.id
    entity_name = instance.insight_logs_verbal
    log_line = f"tenant_id={tenant_id} user_id={user_id} username={username} event_type=entity event_name={event} entity_type={entity_type} entity_id={entity_id} entity_name={entity_name}"  # noqa
    for k, v in kwargs:
        log_line += f' {k}="{v}"'
    insight_logger.info(log_line)


def _insight_diff_finder(before: dict, after: dict):
    before_diff = {}
    after_diff = {}
    for k, v in before.items():
        if after[k] != v:
            before_diff[k] = before[k]
            after_diff[k] = after[k]

    return before_diff, after_diff
