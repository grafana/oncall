from typing import Any, Optional
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

USER_HAS_NO_NOTIFICATION_POLICY = "USER_HAS_NO_NOTIFICATION_POLICY"
USER_IS_NOT_ON_CALL = "USER_IS_NOT_ON_CALL"

# notifications: (User|Schedule, important)
UserNotifications = list[tuple[User, bool]]
ScheduleNotifications = list[tuple[OnCallSchedule, bool]]


def _trigger_alert(
    organization: Organization,
    team: Team,
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
            "verbal_name": f"Direct paging ({team.name if team else 'General'} team)",
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

    payload = {}
    # Custom oncall property in payload to simplify rendering
    payload["oncall"] = {}
    payload["oncall"]["title"] = title
    payload["oncall"]["message"] = message
    # avoid grouping
    payload["oncall"]["uid"] = str(uuid4())
    payload["oncall"]["author_username"] = from_user.username
    payload["oncall"]["permalink"] = permalink
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


def check_user_availability(user: User, team: Team) -> list[dict[str, Any]]:
    """Check user availability to be paged.

    Return a warnings list indicating `error` and any additional related `data`.
    """
    warnings = []
    if not user.notification_policies.exists():
        warnings.append(
            {
                "error": USER_HAS_NO_NOTIFICATION_POLICY,
                "data": {},
            }
        )

    is_on_call = False
    schedules = OnCallSchedule.objects.filter(
        Q(cached_ical_file_primary__contains=user.username) | Q(cached_ical_file_primary__contains=user.email),
        organization=user.organization,
        team=team,
    )
    schedules_data = {}
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
                "error": USER_IS_NOT_ON_CALL,
                "data": {"schedules": schedules_data},
            }
        )

    return warnings


def direct_paging(
    organization: Organization,
    team: Team,
    from_user: User,
    title: str = None,
    message: str = None,
    users: UserNotifications = None,
    schedules: ScheduleNotifications = None,
    escalation_chain: EscalationChain = None,
    alert_group: AlertGroup = None,
) -> Optional[AlertGroup]:
    """Trigger escalation targeting given users/schedules.

    If an alert group is given, update escalation to include the specified users.
    Otherwise, create a new alert using given title and message.

    """
    if not users and not schedules and not escalation_chain:
        return

    if users is None:
        users = []

    if schedules is None:
        schedules = []

    if escalation_chain is not None and alert_group is not None:
        raise ValueError("Cannot change an existing alert group escalation chain")

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
        notify_user_task.apply_async((u.pk, alert_group.pk), {"important": important})

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
