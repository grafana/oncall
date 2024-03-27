import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.google import constants, tasks
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb, ShiftSwapRequest


def _create_mock_google_calendar_event(start_time, end_time):
    return {
        "colorId": "4",
        "created": "2024-03-22T23:06:39.000Z",
        "creator": {
            "email": "joey.orlando@grafana.com",
            "self": True,
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "America/New_York",
        },
        "etag": "3422297608598000",
        "eventType": "outOfOffice",
        "extendedProperties": {
            "private": {
                "reclaim.event.category": "VACATION",
                "reclaim.priority.index": "3",
                "reclaim.project.id": "NULL",
                "reclaim.touched": "true",
            },
        },
        "htmlLink": "https://www.google.com/calendar/event?eid=NDlyZGVmNHU2aTVkaDR1aWFycGZqYWoya3Qgam9leS5vcmxhbmRvQGdyYWZhbmEuY29t",
        "iCalUID": "49rdef4u6i5dh4uiarpfjaj2kt@google.com",
        "id": "49rdef4u6i5dh4uiarpfjaj2kt",
        "kind": "calendar#event",
        "organizer": {
            "email": "joey.orlando@grafana.com",
            "self": True,
        },
        "outOfOfficeProperties": {
            "autoDeclineMode": "declineNone",
        },
        "reminders": {
            "useDefault": False,
        },
        "sequence": 0,
        "start": {
            "dateTime": start_time,
            "timeZone": "America/New_York",
        },
        "status": "confirmed",
        "summary": "Out of office",
        "updated": "2024-03-22T23:06:44.299Z",
        "visibility": "public",
    }


# @pytest.mark.parametrize(
#     "google_calendar_events_api_return_value_items,should_do_something",
#     [
#         # no out of office events
#         # (
#         #     [],
#         #     True,
#         # ),
#         # # all day out of office event
#         # (
#         #     [_create_mock_google_calendar_event(
#         #         "2024-03-26T00:00:00-04:00",
#         #         "2024-03-27T00:00:00-04:00",
#         #     )],
#         #     True,
#         # ),
#         # partial day out of office event
        # (
        #     [

        #     ],
        #     True,
        # ),
#     ],
# )
@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user(
    mock_google_api_client_build,
    make_organization,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
    make_schedule,
    make_on_call_shift,
):
    out_of_office_event = _create_mock_google_calendar_event(
        "2024-03-28T15:30:00-04:00",
        "2024-03-28T16:20:00-04:00",
    )

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": [out_of_office_event],
    }

    organization = make_organization()
    user_name = "Bob Smith"
    user = make_user_for_organization(
        organization,
        # normally this 👇 is done via User.finish_google_oauth2_connection_flow.. but since we're creating
        # the user via a fixture we need to manually add this
        google_calendar_settings={
            "specific_oncall_schedules_to_sync": [],
        },
        name=user_name,
    )
    google_oauth2_user = make_google_oauth2_user_for_user(user)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    dt_format = constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT
    on_call_shift_start = datetime.datetime.strptime(out_of_office_event["start"]["dateTime"], dt_format) - datetime.timedelta(days=60)

    on_call_shift = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        start=on_call_shift_start,
        rotation_start=on_call_shift_start,
        duration=datetime.timedelta(days=365),
        priority_level=1,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        schedule=schedule,
    )
    on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    schedule.refresh_ical_final_schedule()

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    ssrs = ShiftSwapRequest.objects.filter(beneficiary=user, schedule=schedule)
    ssr = ssrs.first()

    assert ssrs.count() == 1

    assert ssr.swap_start == datetime.datetime(2024, 3, 28, 19, 30, 0, tzinfo=timezone.utc)
    assert ssr.swap_end == datetime.datetime(2024, 3, 28, 20, 20, 0, tzinfo=timezone.utc)
    assert ssr.description == f"{user.name} will be out of office during this time according to Google Calendar"


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_multiple_events(
    mock_google_api_client_build,
    make_organization,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
    make_schedule,
    make_on_call_shift,
):
    # TODO:
    pass


def test_sync_out_of_office_calendar_events_for_user_specific_schedules_to_sync_setting():
    # TODO:
    pass


def test_sync_out_of_office_calendar_events_for_user_no_upcoming_shifts():
    # TODO:
    pass


def test_sync_out_of_office_calendar_events_for_user_preexisting_shift_swap_request():
    # TODO:
    pass
