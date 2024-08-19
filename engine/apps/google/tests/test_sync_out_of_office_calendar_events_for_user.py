import datetime
from unittest.mock import call, patch

import pytest
from django.utils import timezone
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from apps.google import constants, tasks
from apps.google.models import GoogleOAuth2User
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb, ShiftSwapRequest


def _create_mock_google_calendar_event(
    start_time: datetime.datetime, end_time: datetime.datetime, summary="Out of office"
):
    return {
        "colorId": "4",
        "created": "2024-03-22T23:06:39.000Z",
        "creator": {
            "email": "joey.orlando@grafana.com",
            "self": True,
        },
        "end": {
            "dateTime": end_time.strftime(constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT),
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
            "dateTime": start_time.strftime(constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT),
            "timeZone": "America/New_York",
        },
        "status": "confirmed",
        "summary": summary,
        "updated": "2024-03-22T23:06:44.299Z",
        "visibility": "public",
    }


def _get_utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _adjust_datetime(dt):
    return dt.replace(second=0, microsecond=0)


def _create_event_start_and_end_times(start_days_in_future=5, end_time_minutes_past_start=50):
    start_time = _adjust_datetime(_get_utc_now() + datetime.timedelta(days=start_days_in_future))
    end_time = start_time + datetime.timedelta(minutes=end_time_minutes_past_start)

    return start_time, end_time


@pytest.fixture
def make_schedule_with_on_call_shift(make_schedule, make_on_call_shift):
    def _make_schedule_with_on_call_shift(out_of_office_events, organization, user):
        schedule = make_schedule(
            organization,
            schedule_class=OnCallScheduleWeb,
            channel="channel",
            prev_ical_file_overrides=None,
            cached_ical_file_overrides=None,
        )

        dt_format = constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT

        if out_of_office_events:
            on_call_shift_start = datetime.datetime.strptime(
                out_of_office_events[0]["start"]["dateTime"], dt_format
            ) - datetime.timedelta(days=60)
        else:
            on_call_shift_start = timezone.now() - datetime.timedelta(days=60)

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

        return schedule

    return _make_schedule_with_on_call_shift


@pytest.fixture
def test_setup(
    make_organization,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
    make_schedule_with_on_call_shift,
):
    def _test_setup(out_of_office_events):
        organization = make_organization()
        user_name = "Bob Smith"
        user = make_user_for_organization(
            organization,
            # normally this 👇 is done via User.save_google_oauth2_settings.. but since we're creating
            # the user via a fixture we need to manually add this
            google_calendar_settings={
                "oncall_schedules_to_consider_for_shift_swaps": [],
            },
            name=user_name,
        )

        google_oauth2_user = make_google_oauth2_user_for_user(user)
        schedule = make_schedule_with_on_call_shift(out_of_office_events, organization, user)

        return google_oauth2_user, schedule

    return _test_setup


class MockResponse:
    def __init__(self, reason=None, status=200) -> None:
        self.reason = reason or ""
        self.status = status


@patch("apps.google.client.build")
@pytest.mark.parametrize(
    "ErrorClass,http_status,should_reset_user_google_oauth2_settings,task_should_raise_exception",
    [
        (RefreshError, None, True, False),
        (HttpError, 401, False, False),
        (HttpError, 500, False, False),
        (HttpError, 403, False, False),
        (Exception, None, False, True),
    ],
)
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_error_scenarios(
    mock_google_api_client_build,
    ErrorClass,
    http_status,
    should_reset_user_google_oauth2_settings,
    task_should_raise_exception,
    test_setup,
):
    if ErrorClass == HttpError:
        mock_response = MockResponse(reason="forbidden", status=http_status)
        exception = ErrorClass(resp=mock_response, content=b"error")
    elif ErrorClass == RefreshError:
        exception = ErrorClass(
            "invalid_grant: Token has been expired or revoked.",
            {"error": "invalid_grant", "error_description": "Token has been expired or revoked."},
        )
    else:
        exception = ErrorClass()

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.side_effect = exception

    google_oauth2_user, schedule = test_setup([])
    user = google_oauth2_user.user

    assert user.google_calendar_settings is not None

    if task_should_raise_exception:
        with pytest.raises(ErrorClass):
            tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)
    else:
        tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

        assert ShiftSwapRequest.objects.filter(beneficiary=user, schedule=schedule).count() == 0

        user.refresh_from_db()

        google_oauth2_user_count = GoogleOAuth2User.objects.filter(user=user).count()

        if should_reset_user_google_oauth2_settings:
            assert user.google_calendar_settings is None
            assert google_oauth2_user_count == 0
        else:
            assert user.google_calendar_settings is not None
            assert google_oauth2_user_count == 1


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_no_ooo_events(mock_google_api_client_build, test_setup):
    out_of_office_events = []

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, schedule = test_setup(out_of_office_events)
    user = google_oauth2_user.user

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert ShiftSwapRequest.objects.filter(beneficiary=user, schedule=schedule).count() == 0


@patch("apps.google.client.build")
@pytest.mark.parametrize(
    "out_of_office_event_title,should_create_ssr",
    [
        ("Out of office", True),
        ("Out of office grafana-oncall-ignore", True),
        ("Out of office #grafana-oncall-ignore", False),
        ("Out of office #GRAFANA-ONCALL-IGNORE", False),
    ],
)
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_single_ooo_event(
    mock_google_api_client_build,
    test_setup,
    out_of_office_event_title,
    should_create_ssr,
):
    start_time, end_time = _create_event_start_and_end_times()
    out_of_office_events = [
        _create_mock_google_calendar_event(start_time, end_time, out_of_office_event_title),
    ]

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, schedule = test_setup(out_of_office_events)
    user = google_oauth2_user.user

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    ssrs = ShiftSwapRequest.objects.filter(beneficiary=user, schedule=schedule)

    if should_create_ssr:
        assert ssrs.count() == 1

        ssr = ssrs.first()

        assert ssr.swap_start == start_time
        assert ssr.swap_end == end_time
        assert ssr.description == f"{user.name} will be out of office during this time according to Google Calendar"
    else:
        assert ssrs.count() == 0


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_multiple_ooo_events(mock_google_api_client_build, test_setup):
    # partial day out of office event
    event1_start_time, event1_end_time = _create_event_start_and_end_times()
    # all day out of office event
    event2_start_time, event2_end_time = _create_event_start_and_end_times(6, 24 * 60)

    out_of_office_events = [
        _create_mock_google_calendar_event(event1_start_time, event1_end_time),
        _create_mock_google_calendar_event(event2_start_time, event2_end_time),
    ]

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, schedule = test_setup(out_of_office_events)
    user = google_oauth2_user.user

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert ShiftSwapRequest.objects.filter(beneficiary=user, schedule=schedule).count() == 2


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_oncall_schedules_to_consider_for_shift_swaps_setting(
    mock_google_api_client_build,
    test_setup,
    make_schedule_with_on_call_shift,
):
    start_time, end_time = _create_event_start_and_end_times()
    out_of_office_events = [
        _create_mock_google_calendar_event(start_time, end_time),
    ]

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, schedule1 = test_setup(out_of_office_events)
    user = google_oauth2_user.user
    make_schedule_with_on_call_shift(out_of_office_events, schedule1.organization, user)

    user.google_calendar_settings = {
        "oncall_schedules_to_consider_for_shift_swaps": [schedule1.public_primary_key],
    }
    user.save()

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert ShiftSwapRequest.objects.filter(beneficiary=user).count() == 1
    ssr = ShiftSwapRequest.objects.first()

    assert ssr.schedule == schedule1


@patch("apps.google.tasks.OnCallSchedule.shifts_for_user", return_value=([], [], []))
@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_no_upcoming_shifts(
    mock_google_api_client_build,
    _mock_schedule_shifts_for_user,
    test_setup,
):
    start_time, end_time = _create_event_start_and_end_times()
    out_of_office_events = [
        _create_mock_google_calendar_event(start_time, end_time),
    ]

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, _ = test_setup(out_of_office_events)
    user = google_oauth2_user.user

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert ShiftSwapRequest.objects.filter(beneficiary=user).count() == 0


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_considers_current_shifts(
    mock_google_api_client_build,
    test_setup,
):
    in_five_minutes = _adjust_datetime(_get_utc_now() + datetime.timedelta(minutes=5))
    in_ten_minutes = in_five_minutes + datetime.timedelta(minutes=5)

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": [
            _create_mock_google_calendar_event(in_five_minutes, in_ten_minutes),
        ],
    }

    google_oauth2_user, _ = test_setup([])
    user = google_oauth2_user.user

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user.pk)

    assert ShiftSwapRequest.objects.filter(beneficiary=user).count() == 1


@patch("apps.google.client.build")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_preexisting_shift_swap_request(
    mock_google_api_client_build,
    test_setup,
    make_shift_swap_request,
):
    start_time, end_time = _create_event_start_and_end_times()
    out_of_office_events = [
        _create_mock_google_calendar_event(start_time, end_time),
    ]

    mock_google_api_client_build.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": out_of_office_events,
    }

    google_oauth2_user, schedule = test_setup(out_of_office_events)
    google_oauth2_user_pk = google_oauth2_user.pk
    user = google_oauth2_user.user

    make_shift_swap_request(
        schedule,
        user,
        swap_start=start_time,
        swap_end=end_time,
    )

    def _fetch_shift_swap_requests():
        return ShiftSwapRequest.objects_with_deleted.filter(beneficiary=user, schedule=schedule)

    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk)

    # should be 1 because we just created a shift swap request above via the fixture
    ssrs = _fetch_shift_swap_requests()
    assert ssrs.count() == 1

    # lets delete the shift swap request and run the task again, it should recognize that there was already
    # a shift swap request and shouldn't recreate a new one
    ssrs.first().delete()
    tasks.sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk)
    assert _fetch_shift_swap_requests().count() == 1


REQUIRED_SCOPE_1 = "https://www.googleapis.com/test/foo"
REQUIRED_SCOPE_2 = "https://www.googleapis.com/test/bar"


@patch("apps.google.tasks.constants.REQUIRED_OAUTH_SCOPES", [REQUIRED_SCOPE_1, REQUIRED_SCOPE_2])
@patch("apps.google.tasks.sync_out_of_office_calendar_events_for_user.apply_async")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_all_users_only_called_for_tokens_having_all_required_scopes(
    mock_sync_out_of_office_calendar_events_for_user,
    make_organization_and_user,
    make_user_for_organization,
    make_google_oauth2_user_for_user,
):
    organization, user1 = make_organization_and_user()
    user2 = make_user_for_organization(organization)
    user3 = make_user_for_organization(organization)

    missing_a_scope = f"{REQUIRED_SCOPE_1} foo_bar"
    has_all_scopes = f"{REQUIRED_SCOPE_1} {REQUIRED_SCOPE_2} foo_bar"

    _ = make_google_oauth2_user_for_user(user1, oauth_scope=missing_a_scope)
    user2_google_oauth2_user = make_google_oauth2_user_for_user(user2, oauth_scope=has_all_scopes)
    user3_google_oauth2_user = make_google_oauth2_user_for_user(user3, oauth_scope=has_all_scopes)

    tasks.sync_out_of_office_calendar_events_for_all_users()

    assert len(mock_sync_out_of_office_calendar_events_for_user.mock_calls) == 2
    mock_sync_out_of_office_calendar_events_for_user.assert_has_calls(
        [
            call(args=(user2_google_oauth2_user.pk,)),
            call(args=(user3_google_oauth2_user.pk,)),
        ],
        any_order=True,
    )


@patch("apps.google.tasks.sync_out_of_office_calendar_events_for_user.apply_async")
@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_all_users_filters_out_users_from_deleted_organizations(
    mock_sync_out_of_office_calendar_events_for_user,
    make_organization_and_user,
    make_google_oauth2_user_for_user,
):
    _, user = make_organization_and_user()
    google_oauth2_user = make_google_oauth2_user_for_user(user)

    deleted_organization, deleted_user = make_organization_and_user()
    make_google_oauth2_user_for_user(deleted_user)
    deleted_organization.delete()

    tasks.sync_out_of_office_calendar_events_for_all_users()
    mock_sync_out_of_office_calendar_events_for_user.assert_called_once_with(args=(google_oauth2_user.pk,))
