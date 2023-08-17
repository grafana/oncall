import enum
import json
import logging

from .insight_logs_enabled_check import is_insight_logs_enabled

insight_logger = logging.getLogger("insight_logger")
logger = logging.getLogger(__name__)


class MaintenanceEvent(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def write_maintenance_insight_log(instance, user, event: MaintenanceEvent):
    try:
        organization = instance.get_organization()

        tenant_id = organization.stack_id
        team = instance.get_team()
        entity_name = json.dumps(instance.insight_logs_verbal)
        entity_id = instance.public_primary_key
        maintenance_mode = instance.get_maintenance_mode_display().lower()

        if is_insight_logs_enabled(organization):
            log_line = f"tenant_id={tenant_id} action_type=maintenance action_name={event.value} maintenance_mode={maintenance_mode} resource_id={entity_id} resource_name={entity_name}"  # noqa
            if team:
                log_line += f" team={json.dumps(team.name)} team_id={team.public_primary_key}"
            else:
                log_line += ' team="General"'
            if user:
                username = json.dumps(user.username)
                user_id = user.public_primary_key
                log_line += f" author_id={user_id} author={username}"
            insight_logger.info(log_line)
    except Exception as e:
        logger.warning(f"insight_log.failed_to_write_maintenance_insight_log exception={e}")
