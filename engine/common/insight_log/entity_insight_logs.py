import enum
import json
import logging
from abc import ABC, abstractmethod

from django.apps import apps

insight_logger = logging.getLogger("insight_logger")
logger = logging.getLogger(__name__)


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

    @property
    @abstractmethod
    def insight_logs_serialized(self) -> dict:
        pass

    @property
    @abstractmethod
    def insight_logs_metadata(self) -> dict:
        pass


def entity_insight_log(instance: InsightLoggable, author, event: EntityEvent, prev_state=None, new_state=None):
    try:
        organization = author.organization
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        org_id_to_enable_insight_logs, _ = DynamicSetting.objects.get_or_create(
            name="org_id_to_enable_insight_logs",
            defaults={"json_value": []},
        )
        insight_logs_enabled = organization.id in org_id_to_enable_insight_logs.json_value
        if insight_logs_enabled:
            tenant_id = organization.stack_id
            author_id = author.public_primary_key
            author = json.dumps(author.username)
            entity_type = instance.insight_logs_type_verbal
            try:
                entity_id = instance.public_primary_key  # Fallback for entities which have no public_primary_key
            except AttributeError:
                entity_id = instance.id
            entity_name = json.dumps(instance.insight_logs_verbal)
            metadata = instance.insight_logs_metadata
            log_line = f"tenant_id={tenant_id} author_id={author_id} author={author} event_type=entity event_name={event.value} entity_type={entity_type} entity_id={entity_id} entity_name={entity_name}"  # noqa
            for k, v in metadata.items():
                log_line += f" {k}={json.dumps(v)}"
            if prev_state and new_state:
                prev_state, new_state = _state_diff_finder(prev_state, new_state)
                prev_state = json.dumps(format_state_for_insight_log(prev_state))
                new_state = json.dumps(format_state_for_insight_log(new_state))
                log_line += f' prev_state="{prev_state}"'
                log_line += f' new_state="{new_state}"'
            insight_logger.info(log_line)
    except Exception as e:
        logger.warning(f"insight_log.failed_to_write_entity_insight_log exception={e}")
        raise e


def _state_diff_finder(before: dict, after: dict):
    before_diff = {}
    after_diff = {}
    for k, v in before.items():
        if k not in after:
            before_diff[k] = v
            continue
        if after[k] != v:
            before_diff[k] = before[k]
            after_diff[k] = after[k]
    for k, v in after.items():
        if k not in before:
            after_diff[k] = v
    return before_diff, after_diff


def format_state_for_insight_log(diff_dict):
    fields_to_prune = ()
    fields_to_hide = ("verified_phone_number", "unverified_phone_number")
    for k, v in diff_dict.items():
        if k in fields_to_prune:
            diff_dict[k] = "Diff not supported"
        if k in fields_to_hide:
            diff_dict[k] = "*****"
    return diff_dict
