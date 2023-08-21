import enum
import typing
from uuid import uuid4

from django.db import transaction
from django.db.models import Q

from apps.alerts.models import (
    Alert,
    AlertGroup,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    ChannelFilter,
    EscalationChain,
    UserHasNotification,
)
from apps.alerts.tasks.notify_user import notify_user_task
from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import Organization, Team, User


class PagingError(enum.StrEnum):
    USER_HAS_NO_NOTIFICATION_POLICY = "USER_HAS_NO_NOTIFICATION_POLICY"
    USER_IS_NOT_ON_CALL = "USER_IS_NOT_ON_CALL"


# notifications: (User|Schedule, important)
UserNotifications = list[tuple[User, bool]]
ScheduleNotifications = list[tuple[OnCallSchedule, bool]]


class NoNotificationPolicyWarning(typing.TypedDict):
    error: typing.Literal[PagingError.USER_HAS_NO_NOTIFICATION_POLICY]
    data: typing.Dict


ScheduleWarnings = typing.Dict[str, typing.List[str]]


class _NotOnCallWarningData(typing.TypedDict):
    schedules: ScheduleWarnings


class NotOnCallWarning(typing.TypedDict):
    error: typing.Literal[PagingError.USER_IS_NOT_ON_CALL]
    data: _NotOnCallWarningData


AvailabilityWarning = NoNotificationPolicyWarning | NotOnCallWarning


class DirectPagingAlertGroupResolvedError(Exception):
    """Raised when trying to use direct paging for a resolved alert group."""

    DETAIL = "Cannot add responders for a resolved alert group"  # Returned in BadRequest responses and Slack warnings


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
    title: str,
    message: str,
    from_user: User,
    escalation_chain: EscalationChain = None,
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
    if alert_receive_channel.default_channel_filter is None:
        ChannelFilter.objects.create(
            alert_receive_channel=alert_receive_channel,
            notify_in_slack=True,
            is_default=True,
        )

    channel_filter = None
    if escalation_chain is not None:
        channel_filter, _ = ChannelFilter.objects.get_or_create(
            alert_receive_channel=alert_receive_channel,
            escalation_chain=escalation_chain,
            is_default=False,
            defaults={
                "filtering_term": f"escalate to {escalation_chain.name}",
                "notify_in_slack": True,
            },
        )

    permalink = None
    if not title:
        title = "Message from {}".format(from_user.username)

    payload: DirectPagingAlertPayload = {
        # Custom oncall property in payload to simplify rendering
        "oncall": {
            "title": title,
            "message": message,
            "uid": str(uuid4()),  # avoid grouping
            "author_username": from_user.username,
            "permalink": permalink,
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


def check_user_availability(user: User) -> typing.List[AvailabilityWarning]:
    """Check user availability to be paged.

    Return a warnings list indicating `error` and any additional related `data`.
    """
    warnings: typing.List[AvailabilityWarning] = []
    if not user.notification_policies.exists():
        warnings.append(
            {
                "error": PagingError.USER_HAS_NO_NOTIFICATION_POLICY,
                "data": {},
            }
        )

    is_on_call = False
    schedules = OnCallSchedule.objects.filter(
        Q(cached_ical_file_primary__contains=user.username) | Q(cached_ical_file_primary__contains=user.email),
        organization=user.organization,
    )
    schedules_data: ScheduleWarnings = {}
    for s in schedules:
        # keep track of schedules and on call users to suggest if needed
        oncall_users = list_users_to_notify_from_ical(s)
        schedules_data[s.name] = set(u.public_primary_key for u in oncall_users)
        if user in oncall_users:
            is_on_call = True
            break

    if not is_on_call:
        # user is not on-call
        # TODO: check working hours
        warnings.append(
            {
                "error": PagingError.USER_IS_NOT_ON_CALL,
                "data": {"schedules": schedules_data},
            }
        )

    return warnings


def direct_paging(
    organization: Organization,
    team: Team | None,
    from_user: User,
    title: str = None,
    message: str = None,
    users: UserNotifications | None = None,
    schedules: ScheduleNotifications | None = None,
    escalation_chain: EscalationChain | None = None,
    alert_group: AlertGroup | None = None,
) -> AlertGroup | None:
    """Trigger escalation targeting given users/schedules.

    If an alert group is given, update escalation to include the specified users.
    Otherwise, create a new alert using given title and message.

    """

    if users is None:
        users = []

    if schedules is None:
        schedules = []

    if escalation_chain is not None and alert_group is not None:
        raise ValueError("Cannot change an existing alert group escalation chain")

    # Cannot add responders to a resolved alert group
    if alert_group and alert_group.resolved:
        raise DirectPagingAlertGroupResolvedError

    # create alert group if needed
    if alert_group is None:
        alert_group = _trigger_alert(organization, team, title, message, from_user, escalation_chain=escalation_chain)

    # initialize direct paged users (without a schedule)
    users = [(u, important, None) for u, important in users]

    # get on call users, add log entry for each schedule
    for s, important in schedules:
        oncall_users = list_users_to_notify_from_ical(s)
        users += [(u, important, s) for u in oncall_users]
        alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
            author=from_user,
            reason=f"{from_user.username} paged schedule {s.name}",
            step_specific_info={"schedule": s.public_primary_key},
        )

    for u, important, schedule in users:
        reason = f"{from_user.username} paged user {u.username}"
        if schedule:
            reason += f" (from schedule {schedule.name})"
        alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
            author=from_user,
            reason=reason,
            step_specific_info={
                "user": u.public_primary_key,
                "schedule": schedule.public_primary_key if schedule else None,
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
            # add log entry
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UNPAGE_USER,
                author=from_user,
                reason=f"{from_user.username} unpaged user {user.username}",
                step_specific_info={"user": user.public_primary_key},
            )
    except IndexError:
        return
