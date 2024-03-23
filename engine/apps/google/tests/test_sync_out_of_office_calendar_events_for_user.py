from unittest.mock import patch

import pytest

from apps.google import tasks


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
    "google_calendar_events_api_return_value",
    [
        # no out of office events
        (
            [],
        ),
        # all day out of office event
        (
            [_create_mock_google_calendar_event(
                "2024-03-26T00:00:00-04:00",
                "2024-03-27T00:00:00-04:00",
            )],
        ),
        # partial day out of office event
        (
            [_create_mock_google_calendar_event(
                "2024-03-28T15:30:00-04:00",
                "2024-03-28T16:20:00-04:00",
            )],
        ),
    ]
)
@patch("apps.google.tasks.GoogleCalendarAPIClient")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user(
    mock_google_calendar_api_client,
    google_calendar_events_api_return_value,
    make_organization,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
):
    mock_google_calendar_api_client.return_value.service.events.return_value.list.return_value.execute.return_value = google_calendar_events_api_return_value

    organization = make_organization()
    user = make_user_for_organization(organization)
    google_oauth2_user = make_google_oauth2_user_for_user(user)

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)
