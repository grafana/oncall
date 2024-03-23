from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.google import constants, tasks
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb


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


@pytest.mark.parametrize(
    "google_calendar_events_api_return_value_items,should_do_something",
    [
        # no out of office events
        # (
        #     [],
        #     True,
        # ),
        # # all day out of office event
        # (
        #     [_create_mock_google_calendar_event(
        #         "2024-03-26T00:00:00-04:00",
        #         "2024-03-27T00:00:00-04:00",
        #     )],
        #     True,
        # ),
        # partial day out of office event
        (
            [
                _create_mock_google_calendar_event(
                    "2024-03-28T15:30:00-04:00",
                    "2024-03-28T16:20:00-04:00",
                )
            ],
            True,
        ),
    ],
)
@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user(
    mock_google_api_client_build,
    google_calendar_events_api_return_value_items,
    should_do_something,
    make_organization,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
    make_schedule,
    make_on_call_shift,
):
    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": google_calendar_events_api_return_value_items,
    }

    organization = make_organization()
    user = make_user_for_organization(organization)
    google_oauth2_user = make_google_oauth2_user_for_user(user)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    if google_calendar_events_api_return_value_items:
        dt_format = constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT
        event = google_calendar_events_api_return_value_items[0]

        calendar_event_start_time = datetime.strptime(event["start"]["dateTime"], dt_format)
        calendar_event_end_time = datetime.strptime(event["end"]["dateTime"], dt_format)

        on_call_shift_start = calendar_event_start_time
        on_call_shift_duration = calendar_event_end_time - calendar_event_start_time
    else:
        on_call_shift_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        on_call_shift_duration = timezone.timedelta(hours=23, minutes=59, seconds=59)

    on_call_shift = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        start=on_call_shift_start,
        rotation_start=on_call_shift_start,
        duration=on_call_shift_duration,
        priority_level=1,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        schedule=schedule,
    )
    on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert True is False
