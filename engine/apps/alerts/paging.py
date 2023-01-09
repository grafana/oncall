import datetime

import pytz

from apps.alerts.models import Alert, AlertGroupLogRecord, AlertReceiveChannel
from apps.alerts.tasks.notify_user import notify_user_task
from apps.schedules.ical_utils import list_users_to_notify_from_ical


def _trigger_alert(organization, team, message, from_user):
    alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
        organization=organization,
        team=team,
        integration=AlertReceiveChannel.INTEGRATION_MANUAL,
        deleted_at=None,
        defaults={
            "author": from_user,
            "verbal_name": f"Manual incidents ({team.name if team else 'General'} team)",
        },
    )

    permalink = None
    title = "Message from {}".format(from_user.username)

    payload = {}
    # Custom oncall property in payload to simplify rendering
    payload["oncall"] = {}
    payload["oncall"]["title"] = title
    payload["oncall"]["message"] = message
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
    )
    return alert.group


# TODO: title should be param
# TODO: alert group could be given? (if we enable escalation for any alert group)
# TODO: priority default/critical?
# TODO: split preview-check + effective paging
def direct_paging(organization, team, from_user, user=None, schedule=None, message=None, important=False, force=False):
    # check user/schedule belongs to org -> API level
    if user is not None and schedule is not None:
        raise ValueError("Only one of user or schedule must be provided")

    # TODO: revisit how to return error/warning
    warning = None

    # TODO: select escalation chain...? setup new channelfilter on the fly?
    #       multiple not possible (alertgroup has FK to channelfilter)

    if schedule:
        users = list_users_to_notify_from_ical(schedule)
        if not users:
            warning = "No user is on call for the schedule"
            return warning
        log_entry = f"{from_user.name} paging schedule {schedule.name}"

    else:
        if not user.notification_policies.exists():
            warning = "User has no notification policy set"
            return warning

        # on call vs in on call rotations
        # in rotations + oncall => ok
        # in rotations + not on call => suggest person on call
        # not in rotations + working hours => suggest schedule
        # in rotations + not working hours => complain a lot

        is_on_call = False
        # check all schedules user belong to? all orgs schedules?
        # how to limit the schedules to check?
        schedules = user.organization.oncall_schedules.filter(team=team)
        for s in schedules:
            oncall_users = list_users_to_notify_from_ical(s)
            if user in oncall_users:
                is_on_call = True
                break

        if not is_on_call:
            # user is not on-call
            # check working hours
            now = datetime.datetime.now(tz=pytz.timezone(user.timezone))
            day_name = now.strftime("%A").lower()

            working_hours = user.working_hours.get(day_name, [])  # this is a list of ranges
            for time_range in working_hours:
                start = time_range.get("start")
                end = time_range.get("end")
                if start and end:
                    start_time = datetime.time(*map(int, start.split(":")), tzinfo=pytz.timezone(user.timezone))
                    end_time = datetime.time(*map(int, end.split(":")), tzinfo=pytz.timezone(user.timezone))
                    if start_time <= now.time() <= end_time:
                        warning = "Use schedules instead"
                        break
            else:
                warning = "User is outside working hours"
                if not force:
                    return warning

        users = [user]
        reason = "User direct paging triggered"
        log_entry = f"{from_user.name} paging user {user.name}"

    alert_group = _trigger_alert(organization, team, message, from_user)
    # TODO: add alert group log record about paging
    alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
        author=from_user,
        reason=log_entry,
        # use specific_info data?
    )
    for u in users:
        notify_user_task.apply_async((u.pk, alert_group.pk), {"reason": reason, "important": important})

    return warning


# QUESTIONS
# enable for any alert group? => replace invite?

# org? get from user? // team: use general? get from schedule?
#   for web: org/team are defined; for chatops: should be params?

# APIs
# - check user availability + return suggestions
# - creation () // should allow multiple users/schedule // diff priority per user/schedule
# - escalate for an existing alert group (which would also allow to add users/schedule to a previous current escalation)
