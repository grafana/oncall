import typing
from functools import partial
from uuid import uuid4

from django.db import transaction

from apps.alerts.models import (
    Alert,
    AlertGroup,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    ChannelFilter,
    UserHasNotification,
)
from apps.alerts.tasks.notify_user import notify_user_task
from apps.schedules.ical_utils import get_cached_oncall_users_for_multiple_schedules
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import Organization, Team, User
from common.utils import escape_html

UserNotifications = list[tuple[User, bool]]


class DirectPagingAlertGroupResolvedError(Exception):
    """Raised when trying to use direct paging for a resolved alert group."""

    DETAIL = "Cannot add responders for a resolved alert group"  # Returned in BadRequest responses and Slack warnings


class DirectPagingUserTeamValidationError(Exception):
    """Raised when trying to use direct paging and no team or user is specified."""

    DETAIL = "No team or user(s) specified"  # Returned in BadRequest responses and Slack warnings


class _OnCall(typing.TypedDict):
    title: str
    message: str
    uid: str
    author_username: str
    permalink: str


class DirectPagingAlertPayload(typing.TypedDict):
    oncall: _OnCall


def _trigger_alert(
    organization: Organization,
    team: Team | None,
    important_team_escalation: bool,
    message: str,
    title: str,
    permalink: str | None,
    grafana_incident_id: str | None,
    from_user: User,
) -> AlertGroup:
    """Trigger manual integration alert from params."""
    alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
        organization=organization,
        team=team,
        integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
        deleted_at=None,
        defaults={
            "author": from_user,
            "verbal_name": f"Direct paging ({team.name if team else 'No'} team)",
        },
    )

    channel_filter = None
    if alert_receive_channel.default_channel_filter is None:
        channel_filter = ChannelFilter.objects.create(
            alert_receive_channel=alert_receive_channel,
            notify_in_slack=True,
            is_default=True,
        )

    payload: DirectPagingAlertPayload = {
        # Custom oncall property in payload to simplify rendering
        "oncall": {
            "title": title,
            "message": message,
            "uid": str(uuid4()),  # avoid grouping
            "author_username": from_user.username,
            "permalink": permalink,
            # NOTE: this field is mostly being added for purposes of escalating to a team
            # this field is provided via the web UI/API/slack as a checkbox, indicating that the user doing the paging
            # would like to send an "important" page to the team.
            #
            # Teams can configure routing in their Direct Paging Integration to route based on this field to different
            # escalation chains
            "important": important_team_escalation,
        },
    }

    alert = Alert.create(
        title=title,
        message=message,
        alert_receive_channel=alert_receive_channel,
        raw_request_data=payload,
        integration_unique_data={"created_by": from_user.username},
        image_url=None,
        link_to_upstream_details=None,
        channel_filter=channel_filter,
    )
    alert_group = alert.group

    if grafana_incident_id is not None:
        alert_group.grafana_incident_id = grafana_incident_id
        alert_group.save(update_fields=["grafana_incident_id"])

    return alert_group


def _construct_title(from_user: User, team: Team | None, users: UserNotifications) -> str:
    title = f"{from_user.username} is paging"

    names = [team.name] if team is not None else []
    names.extend([user.username for user, _ in users])

    if (num_names := len(names)) == 1:
        title += f" {names[0]}"
    elif num_names > 1:
        title += f" {', '.join(names[:-1])} and {names[-1]}"

    title += " to join escalation"

    return title


def direct_paging(
    organization: Organization,
    from_user: User,
    message: str,
    title: str | None = None,
    source_url: str | None = None,
    grafana_incident_id: str | None = None,
    team: Team | None = None,
    important_team_escalation: bool = False,
    users: UserNotifications | None = None,
    alert_group: AlertGroup | None = None,
) -> AlertGroup | None:
    """Trigger escalation targeting given team/users.

    If an alert group is given, update escalation to include the specified users.
    Otherwise, create a new alert using given message.
    """
    if users is None:
        users = []

    if not users and team is None:
        raise DirectPagingUserTeamValidationError

    # Cannot add responders to a resolved alert group
    if alert_group and alert_group.resolved:
        raise DirectPagingAlertGroupResolvedError

    # https://github.com/grafana/oncall-private/issues/2760
    title = escape_html(title)
    message = escape_html(message)

    if title is None:
        title = _construct_title(from_user, team, users)

    # create alert group if needed
    with transaction.atomic():
        if alert_group is None:
            alert_group = _trigger_alert(
                organization,
                team,
                important_team_escalation,
                message,
                title,
                source_url,
                grafana_incident_id,
                from_user,
            )

        for u, important in users:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
                author=from_user,
                reason=f"{from_user.username} paged user {u.username}",
                step_specific_info={
                    "user": u.public_primary_key,
                    "important": important,
                },
            )
            transaction.on_commit(
                partial(
                    notify_user_task.apply_async,
                    (u.pk, alert_group.pk),
                    {"important": important, "notify_even_acknowledged": True, "notify_anyway": True},
                )
            )

    return alert_group


def unpage_user(alert_group: AlertGroup, user: User, from_user: User) -> None:
    """
    Remove user from alert group escalation.

    An IndexError is raised (and caught) if the user had not been notified for some reason.
    Regardless of whether or not the user was notified, we will always create an AlertGroupLogRecord of type
    TYPE_UNPAGE_USER.
    """
    try:
        with transaction.atomic():
            user_has_notification = UserHasNotification.objects.filter(
                user=user, alert_group=alert_group
            ).select_for_update()[0]
            user_has_notification.update_active_task_id(task_id=None)
    except IndexError:
        return
    finally:
        alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_UNPAGE_USER,
            author=from_user,
            reason=f"{from_user.username} unpaged user {user.username}",
            step_specific_info={"user": user.public_primary_key},
        )


def user_is_oncall(user: User) -> bool:
    schedules_with_oncall_users = get_cached_oncall_users_for_multiple_schedules(
        OnCallSchedule.objects.related_to_user(user)
    )
    return user.pk in {user.pk for _, users in schedules_with_oncall_users.items() for user in users}
