import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)

ICAL_URL = "https://calendar.google.com/calendar/ical/amixr.io_37gttuakhrtr75ano72p69rt78%40group.calendar.google.com/private-1d00a680ba5be7426c3eb3ef1616e26d/basic.ics"


@pytest.fixture()
def schedule_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_slack_channel,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    slack_channel = make_slack_channel(
        organization.slack_team_identity,
    )

    calendar_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_calendar_schedule",
    )

    ical_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    web_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    return user, token, calendar_schedule, ical_schedule, web_schedule, slack_channel


@pytest.mark.django_db
def test_get_list_schedules(
    schedule_internal_api_setup, make_escalation_chain, make_escalation_policy, make_user_auth_headers
):
    user, token, calendar_schedule, ical_schedule, web_schedule, slack_channel = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")

    # setup escalation chain linked to web schedule
    escalation_chain = make_escalation_chain(user.organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=web_schedule,
    )

    expected_payload = [
        {
            "id": calendar_schedule.public_primary_key,
            "type": 0,
            "team": None,
            "name": "test_calendar_schedule",
            "time_zone": "UTC",
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "ical_url_overrides": None,
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 0,
        },
        {
            "id": ical_schedule.public_primary_key,
            "type": 1,
            "team": None,
            "name": "test_ical_schedule",
            "ical_url_primary": ICAL_URL,
            "ical_url_overrides": None,
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 0,
        },
        {
            "id": web_schedule.public_primary_key,
            "type": 2,
            "time_zone": "UTC",
            "team": None,
            "name": "test_web_schedule",
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 1,
        },
    ]
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_list_schedules_by_type(
    schedule_internal_api_setup, make_escalation_chain, make_escalation_policy, make_user_auth_headers
):
    user, token, calendar_schedule, ical_schedule, web_schedule, slack_channel = schedule_internal_api_setup
    client = APIClient()

    # setup escalation chain linked to web schedule
    escalation_chain = make_escalation_chain(user.organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=web_schedule,
    )

    expected_payload = [
        {
            "id": calendar_schedule.public_primary_key,
            "type": 0,
            "team": None,
            "name": "test_calendar_schedule",
            "time_zone": "UTC",
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "ical_url_overrides": None,
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 0,
        },
        {
            "id": ical_schedule.public_primary_key,
            "type": 1,
            "team": None,
            "name": "test_ical_schedule",
            "ical_url_primary": ICAL_URL,
            "ical_url_overrides": None,
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 0,
        },
        {
            "id": web_schedule.public_primary_key,
            "type": 2,
            "time_zone": "UTC",
            "team": None,
            "name": "test_web_schedule",
            "slack_channel": None,
            "user_group": None,
            "warnings": [],
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
            "number_of_escalation_chains": 1,
        },
    ]

    for schedule_type in range(3):
        url = reverse("api-internal:schedule-list") + "?type={}".format(schedule_type)
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [expected_payload[schedule_type]]


@pytest.mark.django_db
def test_get_detail_calendar_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, calendar_schedule, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": calendar_schedule.public_primary_key})

    expected_payload = {
        "id": calendar_schedule.public_primary_key,
        "type": 0,
        "team": None,
        "name": "test_calendar_schedule",
        "time_zone": "UTC",
        "slack_channel": None,
        "user_group": None,
        "warnings": [],
        "ical_url_overrides": None,
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
        "number_of_escalation_chains": 0,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_detail_ical_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, ical_schedule, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": ical_schedule.public_primary_key})

    expected_payload = {
        "id": ical_schedule.public_primary_key,
        "team": None,
        "ical_url_primary": ICAL_URL,
        "ical_url_overrides": None,
        "name": "test_ical_schedule",
        "type": 1,
        "slack_channel": None,
        "user_group": None,
        "warnings": [],
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
        "number_of_escalation_chains": 0,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_detail_web_schedule(
    schedule_internal_api_setup, make_escalation_chain, make_escalation_policy, make_user_auth_headers
):
    user, token, _, _, web_schedule, _ = schedule_internal_api_setup
    # setup escalation chain linked to web schedule
    escalation_chain = make_escalation_chain(user.organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=web_schedule,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": web_schedule.public_primary_key})

    expected_payload = {
        "id": web_schedule.public_primary_key,
        "team": None,
        "name": "test_web_schedule",
        "type": 2,
        "time_zone": "UTC",
        "slack_channel": None,
        "user_group": None,
        "warnings": [],
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
        "number_of_escalation_chains": 1,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_create_calendar_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")
    data = {
        "ical_url_overrides": None,
        "type": 0,
        "name": "created_calendar_schedule",
        "time_zone": "UTC",
        "slack_channel_id": None,
        "user_group": None,
        "team": None,
        "warnings": [],
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])
    data["id"] = schedule.public_primary_key
    data["number_of_escalation_chains"] = 0
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == data


@pytest.mark.django_db
def test_create_ical_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")
    with patch(
        "apps.api.serializers.schedule_ical.ScheduleICalSerializer.validate_ical_url_primary", return_value=ICAL_URL
    ):
        data = {
            "ical_url_primary": ICAL_URL,
            "ical_url_overrides": None,
            "name": "created_ical_schedule",
            "type": 1,
            "slack_channel_id": None,
            "user_group": None,
            "team": None,
            "warnings": [],
            "on_call_now": [],
            "has_gaps": False,
            "mention_oncall_next": False,
            "mention_oncall_start": True,
            "notify_empty_oncall": 0,
            "notify_oncall_shift_freq": 1,
        }
        response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
        # modify initial data by adding id and None for optional fields
        schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])
        data["id"] = schedule.public_primary_key
        data["number_of_escalation_chains"] = 0
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == data


@pytest.mark.django_db
def test_create_web_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")
    data = {
        "name": "created_web_schedule",
        "type": 2,
        "time_zone": "UTC",
        "slack_channel_id": None,
        "user_group": None,
        "team": None,
        "warnings": [],
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])
    data["id"] = schedule.public_primary_key
    data["number_of_escalation_chains"] = 0
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == data


@pytest.mark.django_db
def test_create_invalid_ical_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")
    with patch(
        "apps.api.serializers.schedule_ical.ScheduleICalSerializer.validate_ical_url_primary",
        side_effect=ValidationError("Ical download failed"),
    ):
        data = {
            "ical_url_primary": ICAL_URL,
            "ical_url_overrides": None,
            "name": "created_ical_schedule",
            "type": 1,
        }
        response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize("calendar_type", [0, 2])
def test_create_schedule_invalid_time_zone(schedule_internal_api_setup, make_user_auth_headers, calendar_type):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")
    data = {
        "name": "created_web_schedule",
        "type": calendar_type,
        "time_zone": "asdfasdfasdf",
        "slack_channel_id": None,
        "user_group": None,
        "team": None,
        "warnings": [],
        "on_call_now": [],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"time_zone": ["Invalid timezone"]}


@pytest.mark.django_db
def test_update_calendar_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, calendar_schedule, _, _, _ = schedule_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:schedule-detail", kwargs={"pk": calendar_schedule.public_primary_key})
    data = {
        "name": "updated_calendar_schedule",
        "type": 0,
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = OnCallSchedule.objects.get(public_primary_key=calendar_schedule.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "updated_calendar_schedule"


@pytest.mark.django_db
def test_update_ical_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, ical_schedule, _, _ = schedule_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:schedule-detail", kwargs={"pk": ical_schedule.public_primary_key})
    data = {
        "name": "updated_ical_schedule",
        "type": 1,
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = OnCallSchedule.objects.get(public_primary_key=ical_schedule.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "updated_ical_schedule"


@pytest.mark.django_db
def test_update_web_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, web_schedule, _ = schedule_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:schedule-detail", kwargs={"pk": web_schedule.public_primary_key})
    data = {
        "name": "updated_web_schedule",
        "type": 2,
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = OnCallSchedule.objects.get(public_primary_key=web_schedule.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "updated_web_schedule"


@pytest.mark.django_db
@pytest.mark.parametrize("calendar_type", [0, 2])
def test_update_schedule_invalid_time_zone(schedule_internal_api_setup, make_user_auth_headers, calendar_type):
    user, token, *calendars, _ = schedule_internal_api_setup
    schedule = calendars[calendar_type]

    client = APIClient()

    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})
    data = {"name": "updated_web_schedule", "type": calendar_type, "time_zone": "asdfasdfasdf"}
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"time_zone": ["Invalid timezone"]}


@pytest.mark.django_db
def test_delete_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, calendar_schedule, ical_schedule, _, _ = schedule_internal_api_setup
    client = APIClient()

    for calendar in (calendar_schedule, ical_schedule):
        url = reverse("api-internal:schedule-detail", kwargs={"pk": calendar.public_primary_key})
        response = client.delete(url, **make_user_auth_headers(user, token))
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_events_calendar(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_calendar_schedule",
    )

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "priority_level": 2,
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)
    schedule.custom_on_call_shifts.add(on_call_shift)

    url = reverse("api-internal:schedule-events", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_result = {
        "id": schedule.public_primary_key,
        "name": "test_calendar_schedule",
        "type": 0,
        "slack_channel": None,
        "events": [
            {
                "all_day": False,
                "start": on_call_shift.start,
                "end": on_call_shift.start + on_call_shift.duration,
                "users": [{"display_name": user.username, "pk": user.public_primary_key}],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                },
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
def test_filter_events_calendar(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "by_day": ["MO", "FR"],
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )
    on_call_shift.users.add(user)

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?type=rotation"
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    # current week events are expected
    mon_start = now - timezone.timedelta(days=start_date.weekday())
    fri_start = mon_start + timezone.timedelta(days=4)
    expected_result = {
        "id": schedule.public_primary_key,
        "name": "test_web_schedule",
        "type": 2,
        "events": [
            {
                "all_day": False,
                "start": mon_start,
                "end": mon_start + on_call_shift.duration,
                "users": [{"display_name": user.username, "pk": user.public_primary_key}],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                },
            },
            {
                "all_day": False,
                "start": fri_start,
                "end": fri_start + on_call_shift.duration,
                "users": [{"display_name": user.username, "pk": user.public_primary_key}],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                },
            },
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
def test_filter_events_range_calendar(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    mon_start = now - timezone.timedelta(days=start_date.weekday())
    request_date = mon_start + timezone.timedelta(days=2)

    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "by_day": ["MO", "FR"],
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    # add override shift
    override_start = request_date + timezone.timedelta(seconds=3600)
    override_data = {
        "start": override_start,
        "rotation_start": override_start,
        "duration": timezone.timedelta(seconds=3600),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    other_user = make_user_for_organization(organization)
    override.users.add(other_user)

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=3&type=rotation".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    # only friday occurrence is expected
    fri_start = mon_start + timezone.timedelta(days=4)
    expected_result = {
        "id": schedule.public_primary_key,
        "name": "test_web_schedule",
        "type": 2,
        "events": [
            {
                "all_day": False,
                "start": fri_start,
                "end": fri_start + on_call_shift.duration,
                "users": [{"display_name": user.username, "pk": user.public_primary_key}],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                },
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
def test_filter_events_overrides(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    mon_start = now - timezone.timedelta(days=start_date.weekday())
    request_date = mon_start + timezone.timedelta(days=2)

    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "by_day": ["MO", "FR"],
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    # add override shift
    override_start = request_date + timezone.timedelta(seconds=3600)
    override_data = {
        "start": override_start,
        "rotation_start": override_start,
        "duration": timezone.timedelta(seconds=3600),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    other_user = make_user_for_organization(organization)
    override.add_rolling_users([[other_user]])

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=3&type=override".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    # only override occurrence is expected
    expected_result = {
        "id": schedule.public_primary_key,
        "name": "test_web_schedule",
        "type": 2,
        "events": [
            {
                "all_day": False,
                "start": override_start,
                "end": override_start + override.duration,
                "users": [{"display_name": other_user.username, "pk": other_user.public_primary_key}],
                "missing_users": [],
                "priority_level": None,
                "source": "api",
                "calendar_type": OnCallSchedule.OVERRIDES,
                "is_empty": False,
                "is_gap": False,
                "is_override": True,
                "shift": {
                    "pk": override.public_primary_key,
                },
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
def test_filter_events_final_schedule(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    request_date = start_date

    user_a, user_b, user_c, user_d, user_e = (make_user_for_organization(organization, username=i) for i in "ABCDE")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 10, 5),  # r1-1: 10-15 / A
        (user_b, 1, 11, 2),  # r1-2: 11-13 / B
        (user_a, 1, 16, 3),  # r1-3: 16-19 / A
        (user_a, 1, 21, 1),  # r1-4: 21-22 / A
        (user_b, 1, 22, 2),  # r1-5: 22-00 / B
        (user_c, 2, 12, 2),  # r2-1: 12-14 / C
        (user_d, 2, 14, 1),  # r2-2: 14-15 / D
        (user_d, 2, 17, 1),  # r2-3: 17-18 / D
        (user_d, 2, 20, 3),  # r2-4: 20-23 / D
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date,
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    # override: 22-23 / E
    override_data = {
        "start": start_date + timezone.timedelta(hours=22),
        "rotation_start": start_date + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_e]])

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=1".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    expected = (
        # start (h), duration (H), user, priority, is_gap, is_override
        (0, 10, None, None, True, False),  # 0-10 gap
        (10, 2, "A", 1, False, False),  # 10-12 A
        (11, 1, "B", 1, False, False),  # 11-12 B
        (12, 2, "C", 2, False, False),  # 12-14 C
        (14, 1, "D", 2, False, False),  # 14-15 D
        (15, 1, None, None, True, False),  # 15-16 gap
        (16, 1, "A", 1, False, False),  # 16-17 A
        (17, 1, "D", 2, False, False),  # 17-18 D
        (18, 1, "A", 1, False, False),  # 18-19 A
        (19, 1, None, None, True, False),  # 19-20 gap
        (20, 2, "D", 2, False, False),  # 20-22 D
        (22, 1, "E", None, False, True),  # 22-23 E (override)
        (23, 1, "B", 1, False, False),  # 23-00 B
    )
    expected_events = [
        {
            "calendar_type": 1 if is_override else None if is_gap else 0,
            "end": start_date + timezone.timedelta(hours=start + duration),
            "is_gap": is_gap,
            "is_override": is_override,
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
            "user": user,
        }
        for start, duration, user, priority, is_gap, is_override in expected
    ]
    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_gap": e["is_gap"],
            "is_override": e["is_override"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in response.data["events"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_next_shifts_per_user(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    user_a, user_b, user_c, user_d = (make_user_for_organization(organization, username=i) for i in "ABCD")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 8, 2),  # r1-1: 8-10 / A
        (user_a, 1, 15, 2),  # r1-2: 15-17 / A
        (user_b, 2, 7, 5),  # r2-1: 7-12 / B
        (user_b, 2, 16, 2),  # r2-2: 16-18 / B
        (user_c, 2, 18, 2),  # r2-3: 18-20 / C
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": tomorrow + timezone.timedelta(hours=start_h),
            "rotation_start": tomorrow + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    # override in the past: 17-18 / D
    # won't be listed, but user D will still be included in the response
    override_data = {
        "start": tomorrow - timezone.timedelta(days=3),
        "rotation_start": tomorrow - timezone.timedelta(days=3),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_d]])

    # override: 17-18 / C
    override_data = {
        "start": tomorrow + timezone.timedelta(hours=17),
        "rotation_start": tomorrow + timezone.timedelta(hours=17),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_c]])

    # final schedule: 7-12: B, 15-16: A, 16-17: B, 17-18: C (override), 18-20: C

    url = reverse("api-internal:schedule-next-shifts-per-user", kwargs={"pk": schedule.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK

    expected = {
        user_a.public_primary_key: (tomorrow + timezone.timedelta(hours=15), tomorrow + timezone.timedelta(hours=16)),
        user_b.public_primary_key: (tomorrow + timezone.timedelta(hours=7), tomorrow + timezone.timedelta(hours=12)),
        user_c.public_primary_key: (tomorrow + timezone.timedelta(hours=17), tomorrow + timezone.timedelta(hours=18)),
        user_d.public_primary_key: None,
    }
    returned_data = {
        u: (ev["start"], ev["end"]) if ev is not None else None for u, ev in response.data["users"].items()
    }
    assert returned_data == expected


@pytest.mark.django_db
def test_related_escalation_chains(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_escalation_chain,
    make_escalation_policy,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    # setup escalation chains linked to web schedule
    escalation_chains = []
    for i in range(3):
        chain = make_escalation_chain(user.organization)
        make_escalation_policy(
            escalation_chain=chain,
            escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
            notify_schedule=schedule,
        )
        escalation_chains.append(chain)
    # setup other unrelated schedule
    other_schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    other_chain = make_escalation_chain(user.organization)
    make_escalation_policy(
        escalation_chain=other_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=other_schedule,
    )

    url = reverse("api-internal:schedule-related-escalation-chains", kwargs={"pk": schedule.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    expected = [{"name": chain.name, "pk": chain.public_primary_key} for chain in escalation_chains]
    assert sorted(response.data, key=lambda e: e["name"]) == sorted(expected, key=lambda e: e["name"])


@pytest.mark.django_db
def test_merging_same_shift_events(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    request_date = start_date + timezone.timedelta(days=1)

    user_a = make_user_for_organization(organization)
    user_b = make_user_for_organization(organization)
    user_c = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    data = {
        "start": start_date + timezone.timedelta(hours=10),
        "rotation_start": start_date + timezone.timedelta(hours=10),
        "duration": timezone.timedelta(hours=2),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user_a, user_c, user_b]])

    expected_events = [
        {
            "calendar_type": 0,
            "end": request_date + timezone.timedelta(hours=12),
            "is_gap": False,
            "priority_level": 1,
            "start": request_date + timezone.timedelta(hours=10),
            "users": sorted([user_a.username, user_b.username]),
            "missing_users": [user_c.username],
        }
    ]

    # final schedule
    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=1".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_gap": e["is_gap"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "users": sorted([u["display_name"] for u in e["users"]]) if e["users"] else None,
            "missing_users": e["missing_users"],
        }
        for e in response.data["events"]
        if not e["is_gap"]
    ]
    assert returned_events == expected_events

    # rotations
    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=1&type=rotation".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_gap": e["is_gap"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "users": sorted([u["display_name"] for u in e["users"]]) if e["users"] else None,
            "missing_users": e["missing_users"],
        }
        for e in response.data["events"]
        if not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_filter_events_invalid_type(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?type=invalid"
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-list")

    with patch(
        "apps.api.views.schedule.ScheduleView.create",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.update",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status

        response = client.patch(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-list")

    with patch(
        "apps.api.views.schedule.ScheduleView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.destroy",
        return_value=Response(
            status=status.HTTP_204_NO_CONTENT,
        ),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_events_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-events", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.events",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_reload_ical_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-reload-ical", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.reload_ical",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_notify_oncall_shift_freq_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    url = reverse("api-internal:schedule-notify-oncall-shift-freq-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_notify_empty_oncall_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    url = reverse("api-internal:schedule-notify-empty-oncall-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_mention_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    url = reverse("api-internal:schedule-mention-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_get_schedule_from_other_team_with_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    calendar_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_calendar_schedule",
        team=team,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": calendar_schedule.public_primary_key})
    url = f"{url}?from_organization=true"

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_schedule_from_other_team_without_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    calendar_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_calendar_schedule",
        team=team,
    )

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": calendar_schedule.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN
