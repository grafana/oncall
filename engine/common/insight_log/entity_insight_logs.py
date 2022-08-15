import enum
import json
import logging
from abc import ABC, abstractmethod

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
        tenant_id = organization.stack_id
        author_id = author.public_primary_key
        author = author.username
        entity_type = instance.insight_logs_type_verbal
        try:
            entity_id = instance.public_primary_key  # Fallback for entities which have no public_primary_key
        except AttributeError:
            entity_id = instance.id
        entity_name = instance.insight_logs_verbal
        metadata = instance.insight_logs_metadata
        log_line = f"tenant_id={tenant_id} author_id={author_id} author={author} event_type=entity event_name={event} entity_type={entity_type} entity_id={entity_id} entity_name={entity_name}"  # noqa
        for k, v in metadata.items():
            log_line += f' {k}="{v}"'
        if prev_state and new_state:
            prev_state, new_state = _state_diff_finder(prev_state, new_state)
            prev_state = json.dumps(format_state_for_insight_log(prev_state))
            new_state = json.dumps(format_state_for_insight_log(new_state))
            log_line += f" prev_state={prev_state}"
            log_line += f" new_state={new_state}"
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
    fields_to_prune = (
        "slack_title",
        "slack_message",
        "slack_image_url",
        "sms_title",
        "phone_call_title",
        "web_title",
        "web_message",
        "web_image_url_template",
        "email_title_template",
        "email_message",
        "telegram_title",
        "telegram_message",
        "telegram_image_url",
        "source_link",
        "grouping_id",
        "resolve_condition",
        "acknowledge_condition",
    )
    fields_to_hide = ()
    for k, v in diff_dict.items():
        if k in fields_to_prune:
            pass
            # diff_dict[k] = "Diff not supported"
        if k in fields_to_hide:
            pass
    return diff_dict
