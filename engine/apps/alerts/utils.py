import typing

from django.conf import settings

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


def render_relative_timeline(log_created_at, alert_group_started_at):
    time_delta = log_created_at - alert_group_started_at
    seconds = int(time_delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%dd%dh%dm%ds" % (days, hours, minutes, seconds)
    elif hours > 0:
        return "%dh%dm%ds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%dm%ds" % (minutes, seconds)
    else:
        return "%ds" % (seconds,)


def is_declare_incident_step_enabled(organization: "Organization") -> bool:
    return organization.is_grafana_incident_enabled and settings.FEATURE_DECLARE_INCIDENT_STEP_ENABLED
