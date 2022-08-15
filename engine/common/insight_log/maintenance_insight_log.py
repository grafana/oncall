import enum
import logging

insight_logger = logging.getLogger("insight_logger")


class MaintenanceEvent(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def maintenance_insight_log(instance, user, event: MaintenanceEvent):
    organization = instance.get_organization()
    tenant_id = organization.stack_id
    team = instance.get_team()
    entity_name = instance.insight_logs_verbal
    entity_id = instance.public_primary_key
    maintenance_mode = instance.get_maintenance_mode_display()
    log_line = f"tenant_id={tenant_id} event_type=maintenance event_name={event} maintenance_mode={maintenance_mode} entity_id={entity_id} entity_name={entity_name}"  # noqa
    if team:
        log_line += f" team={team.insight_logs_verbal} team_id={team.public_primary_key}"
    if user:
        username = user.username
        user_id = user.public_primary_key
        log_line += f" user_id={user_id} username={username} "
    insight_logger.info(log_line)
