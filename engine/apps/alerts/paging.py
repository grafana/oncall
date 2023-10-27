import typing
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
from apps.schedules.ical_utils import get_oncall_users_for_multiple_schedules
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import Organization, Team, User

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
    organization: Organization, team: Team | None, message: str, title: str, from_user: User
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
            "permalink": None,
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
    return alert.group


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
    team: Team | None = None,
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

    if title is None:
        title = _construct_title(from_user, team, users)

    # create alert group if needed
    if alert_group is None:
        alert_group = _trigger_alert(organization, team, message, title, from_user)

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
        notify_user_task.apply_async(
            (u.pk, alert_group.pk), {"important": important, "notify_even_acknowledged": True, "notify_anyway": True}
        )

    return alert_group


def unpage_user(alert_group: AlertGroup, user: User, from_user: User) -> None:
    """Remove user from alert group escalation."""
    try:
        with transaction.atomic():
            user_has_notification = UserHasNotification.objects.filter(
                user=user, alert_group=alert_group
            ).select_for_update()[0]
            user_has_notification.active_notification_policy_id = None
            user_has_notification.save(update_fields=["active_notification_policy_id"])
    except IndexError:
        return
    finally:
        # add log entry
        alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_UNPAGE_USER,
            author=from_user,
            reason=f"{from_user.username} unpaged user {user.username}",
            step_specific_info={"user": user.public_primary_key},
        )


def user_is_oncall(user: User) -> bool:
    schedules_with_oncall_users = get_oncall_users_for_multiple_schedules(OnCallSchedule.objects.related_to_user(user))
    return user.pk in {user.pk for _, users in schedules_with_oncall_users.items() for user in users}


def integration_is_notifiable(integration: AlertReceiveChannel) -> bool:
    """
    Returns true if:
    - the integration has more than one channel filter associated with it
    - the default channel filter has at least one notification method specified or an escalation chain associated with it
    """
    if integration.channel_filters.count() > 1:
        return True

    default_channel_filter = integration.default_channel_filter
    if not default_channel_filter:
        return False

    organization = integration.organization
    notify_via_slack = organization.slack_is_configured and default_channel_filter.notify_in_slack
    notify_via_telegram = organization.telegram_is_configured and default_channel_filter.notify_in_telegram

    notify_via_chatops = notify_via_slack or notify_via_telegram
    custom_messaging_backend_configured = default_channel_filter.notification_backends is not None

    return (
        default_channel_filter.escalation_chain is not None or notify_via_chatops or custom_messaging_backend_configured
    )
