import enum
import json
import logging
import re
from abc import ABC, abstractmethod

from .insight_logs_enabled_check import is_insight_logs_enabled

insight_logger = logging.getLogger("insight_logger")
logger = logging.getLogger(__name__)


class EntityEvent(enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class InsightLoggable(ABC):
    @property
    @abstractmethod
    def id(self) -> int:
        pass

    @property
    @abstractmethod
    def public_primary_key(self) -> str:
        pass

    @property
    @abstractmethod
    def insight_logs_verbal(self) -> str:
        """
        insight_logs_verbal returns resource name for insight_log
        """
        pass

    @property
    @abstractmethod
    def insight_logs_type_verbal(self) -> str:
        """
        insight_logs_type_verbal resource type for insight_log
        """
        pass

    @property
    @abstractmethod
    def insight_logs_serialized(self) -> dict:
        """
        insight_logs_serialized returns resource, serialized for insight_log
        """
        pass

    @property
    @abstractmethod
    def insight_logs_metadata(self) -> dict:
        """
        insight_logs_metadata returns resource's fields which should be always present in the insight_log line even if
        they weren't changed
        """
        pass


def write_resource_insight_log(instance: InsightLoggable, author, event: EntityEvent, prev_state=None, new_state=None):
    try:
        organization = author.organization
        if is_insight_logs_enabled(organization):
            tenant_id = organization.stack_id
            author_id = author.public_primary_key
            author = json.dumps(author.username)
            entity_type = instance.insight_logs_type_verbal
            try:
                entity_id: str | int = instance.public_primary_key
            except AttributeError:
                # Fallback for entities which have no public_primary_key, E.g. public api token, schedule export token
                entity_id = instance.id
            entity_name = json.dumps(instance.insight_logs_verbal)
            metadata = instance.insight_logs_metadata
            log_line = f"tenant_id={tenant_id} author_id={author_id} author={author} action_type=resource action_name={event.value} resource_type={entity_type} resource_id={entity_id} resource_name={entity_name}"  # noqa
            for k, v in metadata.items():
                log_line += f" {k}={json.dumps(v)}"
            if prev_state and new_state:
                prev_state, new_state = state_diff_finder(prev_state, new_state)
                prev_state = escape_json_str_for_insight_log(json.dumps(format_state_for_insight_log(prev_state)))
                new_state = escape_json_str_for_insight_log(json.dumps(format_state_for_insight_log(new_state)))
                log_line += f' prev_state="{prev_state}"'
                log_line += f' new_state="{new_state}"'
            insight_logger.info(log_line)
    except Exception as e:
        logger.warning(f"insight_log.failed_to_write_entity_insight_log exception={e} instance_id={instance.id}")


def state_diff_finder(prev_state: dict, new_state: dict):
    """
    state_diff_finder returns diff between two serialized representations of the resource
    """
    before_diff = {}
    after_diff = {}
    for k, v in prev_state.items():
        if k not in new_state:
            before_diff[k] = v
            continue
        if new_state[k] != v:
            before_diff[k] = prev_state[k]
            after_diff[k] = new_state[k]
    for k, v in new_state.items():
        if k not in prev_state:
            after_diff[k] = v
    return before_diff, after_diff


def escape_json_str_for_insight_log(string):
    """
    escape_json_str escapes double quotes near keys and values in json string
    """
    return re.sub(r"(?<!\\)(\")", r"\\\1", string)


def format_state_for_insight_log(diff_dict):
    """
    format_state_for_insight_log formats serialized resource data for the insight log.
    It hides and prunes fields which shouldn't be exposed
    """
    fields_to_prune = ()
    fields_to_hide = ("verified_phone_number", "unverified_phone_number")
    for k, v in diff_dict.items():
        if k in fields_to_prune:
            diff_dict[k] = "Diff not supported"
        if k in fields_to_hide:
            diff_dict[k] = "*****"
    return diff_dict
