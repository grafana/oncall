import json
import textwrap
from unittest.mock import PropertyMock, patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole
from apps.api.serializers.schedule_base import ScheduleBaseSerializer
from apps.api.serializers.user import ScheduleUserSerializer
from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)
from apps.slack.models import SlackUserGroup
from common.api_helpers.utils import create_engine_url, serialize_datetime_as_utc_timestamp

ICAL_URL = "https://calendar.google.com/calendar/ical/amixr.io_37gttuakhrtr75ano72p69rt78%40group.calendar.google.com/private-1d00a680ba5be7426c3eb3ef1616e26d/basic.ics"


@pytest.fixture()
def schedule_internal_api_setup(
    make_organization_and_user_with_plugin_token,
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

    expected_payload = {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
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
                "enable_web_overrides": False,
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
                "enable_web_overrides": False,
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
                "enable_web_overrides": True,
            },
        ],
        "current_page_number": 1,
        "page_size": 15,
        "total_pages": 1,
    }
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_list_schedules_pagination(
    schedule_internal_api_setup, make_escalation_chain, make_escalation_policy, make_user_auth_headers
):
    user, token, calendar_schedule, ical_schedule, web_schedule, _ = schedule_internal_api_setup

    # setup escalation chain linked to web schedule
    escalation_chain = make_escalation_chain(user.organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=web_schedule,
    )

    available_schedules = [
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
            "enable_web_overrides": False,
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
            "enable_web_overrides": False,
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
            "enable_web_overrides": True,
        },
    ]

    client = APIClient()

    schedule_list_url = reverse("api-internal:schedule-list")
    absolute_url = create_engine_url(schedule_list_url)
    for p, schedule in enumerate(available_schedules, start=1):
        # patch oncall_users to check a paginated queryset is used
        def mock_oncall_now(qs, events_datetime):
            # only one schedule is passed here
            assert qs.count() == 1
            return {}

        url = "{}?page={}&perpage=1".format(schedule_list_url, p)
        with patch(
            "apps.schedules.models.on_call_schedule.get_oncall_users_for_multiple_schedules",
            side_effect=mock_oncall_now,
        ):
            response = client.get(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == status.HTTP_200_OK
        previous_url = None
        next_url = "{}?page={}&perpage=1".format(absolute_url, p + 1)
        if p == 2:
            previous_url = "{}?perpage=1".format(absolute_url)
        elif p > 2:
            previous_url = "{}?page={}&perpage=1".format(absolute_url, p - 1)
            next_url = None
        expected_payload = {
            "count": 3,
            "next": next_url,
            "previous": previous_url,
            "results": [schedule],
            "current_page_number": p,
            "page_size": 1,
            "total_pages": 3,
        }
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

    available_schedules = [
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
            "enable_web_overrides": False,
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
            "enable_web_overrides": False,
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
            "enable_web_overrides": True,
        },
    ]

    for schedule_type in range(3):
        url = reverse("api-internal:schedule-list") + "?type={}".format(schedule_type)
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == status.HTTP_200_OK
        expected_payload = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [available_schedules[schedule_type]],
            "current_page_number": 1,
            "page_size": 15,
            "total_pages": 1,
        }
        assert response.json() == expected_payload

    # request multiple types
    url = reverse("api-internal:schedule-list") + "?type=0&type=1"
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_payload = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [available_schedules[0], available_schedules[1]],
        "current_page_number": 1,
        "page_size": 15,
        "total_pages": 1,
    }
    assert response.json() == expected_payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query_param, expected_schedule_names",
    [
        ("?used=true", ["test_web_schedule"]),
        ("?used=false", ["test_calendar_schedule", "test_ical_schedule"]),
        ("?used=null", ["test_calendar_schedule", "test_ical_schedule", "test_web_schedule"]),
        ("", ["test_calendar_schedule", "test_ical_schedule", "test_web_schedule"]),
    ],
)
def test_get_list_schedules_by_used(
    schedule_internal_api_setup,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    query_param,
    expected_schedule_names,
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

    url = reverse("api-internal:schedule-list") + query_param
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == len(expected_schedule_names)

    schedule_names = [schedule["name"] for schedule in response.json()["results"]]
    assert set(schedule_names) == set(expected_schedule_names)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query_param, expected_schedule_names",
    [
        ("?mine=true", ["test_web_schedule"]),
        ("?mine=false", ["test_calendar_schedule", "test_ical_schedule", "test_web_schedule"]),
        ("?mine=null", ["test_calendar_schedule", "test_ical_schedule", "test_web_schedule"]),
        ("", ["test_calendar_schedule", "test_ical_schedule", "test_web_schedule"]),
    ],
)
def test_get_list_schedules_by_mine(
    schedule_internal_api_setup,
    make_user_auth_headers,
    make_on_call_shift,
    query_param,
    expected_schedule_names,
):
    user, token, calendar_schedule, ical_schedule, web_schedule, slack_channel = schedule_internal_api_setup
    client = APIClient()

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # setup user shift in web schedule
    override_data = {
        "start": today + timezone.timedelta(hours=22),
        "rotation_start": today + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": web_schedule,
    }
    override = make_on_call_shift(
        organization=user.organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user]])
    web_schedule.refresh_ical_file()

    url = reverse("api-internal:schedule-list") + query_param
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == len(expected_schedule_names)

    schedule_names = [schedule["name"] for schedule in response.json()["results"]]
    assert set(schedule_names) == set(expected_schedule_names)


@pytest.mark.django_db
def test_get_list_schedules_pagination_respects_search(
    schedule_internal_api_setup,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
):
    user, token, _, _, _, _ = schedule_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:schedule-list") + "?search=ical"
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert len(response.json()["results"]) == 1


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
        "enable_web_overrides": False,
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
        "enable_web_overrides": False,
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
        "enable_web_overrides": True,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_detail_schedule_oncall_now_multipage_objects(
    make_organization_and_user_with_plugin_token, make_schedule, make_on_call_shift, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    # make sure our schedule would be in the second page of the listing page
    for i in range(16):
        make_schedule(organization, schedule_class=OnCallScheduleWeb, name=f"schedule {i}")

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=86400),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})

    expected_payload = {
        "id": schedule.public_primary_key,
        "team": None,
        "name": "test_web_schedule",
        "type": 2,
        "time_zone": "UTC",
        "slack_channel": None,
        "user_group": None,
        "warnings": [],
        "on_call_now": [
            {
                "pk": user.public_primary_key,
                "username": user.username,
                "avatar": user.avatar_url,
                "avatar_full": user.avatar_full_url,
            }
        ],
        "has_gaps": False,
        "mention_oncall_next": False,
        "mention_oncall_start": True,
        "notify_empty_oncall": 0,
        "notify_oncall_shift_freq": 1,
        "number_of_escalation_chains": 0,
        "enable_web_overrides": True,
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
        "enable_web_overrides": True,
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
    with patch(
        "apps.api.serializers.schedule_ical.ScheduleICalSerializer.validate_ical_url_primary", return_value=ICAL_URL
    ), patch("apps.schedules.tasks.refresh_ical_final_schedule.apply_async") as mock_refresh_final:
        response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
        # modify initial data by adding id and None for optional fields
        schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])
        data["id"] = schedule.public_primary_key
        data["number_of_escalation_chains"] = 0
        data["enable_web_overrides"] = False
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == data
        # check final schedule refresh triggered
        mock_refresh_final.assert_called_once_with((schedule.pk,))


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
    data["enable_web_overrides"] = True
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == data


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
    with patch("apps.schedules.tasks.refresh_ical_final_schedule.apply_async") as mock_refresh_final:
        response = client.put(
            url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
        )
    updated_instance = OnCallSchedule.objects.get(public_primary_key=ical_schedule.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "updated_ical_schedule"
    # check refresh final is not triggered (url unchanged)
    assert not mock_refresh_final.called


@pytest.mark.django_db
def test_update_ical_schedule_url(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, ical_schedule, _, _ = schedule_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:schedule-detail", kwargs={"pk": ical_schedule.public_primary_key})

    updated_url = "another-url"
    data = {
        "name": ical_schedule.name,
        "type": 1,
        "ical_url_primary": updated_url,
    }
    with patch(
        "apps.api.serializers.schedule_ical.ScheduleICalSerializer.validate_ical_url_primary", return_value=updated_url
    ), patch("apps.schedules.tasks.refresh_ical_final_schedule.apply_async") as mock_refresh_final:
        response = client.put(
            url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
        )
    updated_instance = OnCallSchedule.objects.get(public_primary_key=ical_schedule.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    # check refresh final triggered (changing url)
    mock_refresh_final.assert_called_once_with((updated_instance.pk,))


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
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                        "email": user.email,
                        "avatar_full": user.avatar_full_url,
                    },
                ],
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
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                        "email": user.email,
                        "avatar_full": user.avatar_full_url,
                    },
                ],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                    "name": on_call_shift.name,
                    "type": on_call_shift.type,
                },
            },
            {
                "all_day": False,
                "start": fri_start,
                "end": fri_start + on_call_shift.duration,
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                        "email": user.email,
                        "avatar_full": user.avatar_full_url,
                    }
                ],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                    "name": on_call_shift.name,
                    "type": on_call_shift.type,
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
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                        "email": user.email,
                        "avatar_full": user.avatar_full_url,
                    },
                ],
                "missing_users": [],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "is_override": False,
                "shift": {
                    "pk": on_call_shift.public_primary_key,
                    "name": on_call_shift.name,
                    "type": on_call_shift.type,
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
                "users": [
                    {
                        "display_name": other_user.username,
                        "pk": other_user.public_primary_key,
                        "email": other_user.email,
                        "avatar_full": other_user.avatar_full_url,
                    }
                ],
                "missing_users": [],
                "priority_level": None,
                "source": "api",
                "calendar_type": OnCallSchedule.OVERRIDES,
                "is_empty": False,
                "is_gap": False,
                "is_override": True,
                "shift": {
                    "pk": override.public_primary_key,
                    "name": override.name,
                    "type": override.type,
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
            "start": start_date + timezone.timedelta(hours=start),
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
def test_filter_swap_requests(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_shift_swap_request,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    other_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="other_web_schedule",
    )
    user_a, user_b, user_c = (make_user_for_organization(organization, username=i) for i in "ABC")

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timezone.timedelta(days=7)
    request_date = start_date

    # swap for other schedule
    make_shift_swap_request(
        other_schedule,
        user_a,
        swap_start=start_date + timezone.timedelta(days=1),
        swap_end=start_date + timezone.timedelta(days=3),
    )
    # swap out of range
    make_shift_swap_request(
        schedule,
        user_a,
        swap_start=start_date + timezone.timedelta(days=10),
        swap_end=start_date + timezone.timedelta(days=13),
    )
    # expected swaps
    swap_a = make_shift_swap_request(
        schedule,
        user_a,
        swap_start=start_date + timezone.timedelta(days=1),
        swap_end=start_date + timezone.timedelta(days=3),
    )
    swap_b = make_shift_swap_request(
        schedule,
        user_b,
        swap_start=start_date,
        swap_end=start_date + timezone.timedelta(days=1),
        benefactor=user_c,
    )

    url = reverse("api-internal:schedule-filter-shift-swaps", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=1".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK

    def _serialized_user(u):
        if u:
            return {
                "display_name": u.username,
                "email": u.email,
                "pk": u.public_primary_key,
                "avatar_full": u.avatar_full_url,
            }

    expected = [
        {
            "pk": swap.public_primary_key,
            "swap_start": serialize_datetime_as_utc_timestamp(swap.swap_start),
            "swap_end": serialize_datetime_as_utc_timestamp(swap.swap_end),
            "beneficiary": _serialized_user(swap.beneficiary),
            "benefactor": _serialized_user(swap.benefactor),
        }
        for swap in (swap_a, swap_b)
    ]
    returned = [
        {
            "pk": s["id"],
            "swap_start": s["swap_start"],
            "swap_end": s["swap_end"],
            "beneficiary": s["beneficiary"],
            "benefactor": s["benefactor"],
        }
        for s in response.data["shift_swaps"]
    ]
    assert returned == expected


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
    users = (
        ("A", "Europe/London"),
        ("B", "UTC"),
        ("C", None),
        ("D", "America/Montevideo"),
    )
    user_a, user_b, user_c, user_d = (
        make_user_for_organization(organization, username=i, _timezone=tz) for i, tz in users
    )

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
        user_a.public_primary_key: (
            tomorrow + timezone.timedelta(hours=15),
            tomorrow + timezone.timedelta(hours=16),
            user_a.timezone,
        ),
        user_b.public_primary_key: (
            tomorrow + timezone.timedelta(hours=7),
            tomorrow + timezone.timedelta(hours=12),
            user_b.timezone,
        ),
        user_c.public_primary_key: (
            tomorrow + timezone.timedelta(hours=17),
            tomorrow + timezone.timedelta(hours=18),
            user_c.timezone,
        ),
        user_d.public_primary_key: (None, None, user_d.timezone),
    }
    returned_data = {
        u: (ev.get("start"), ev.get("end"), ev.get("user_timezone")) for u, ev in response.data["users"].items()
    }
    assert returned_data == expected


@pytest.mark.django_db
def test_next_shifts_per_user_ical_schedule_using_emails(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers, make_schedule
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    user = make_user_for_organization(organization, username="testing", email="testing@testing.com")
    # ical file using emails as reference
    cached_ical_primary_schedule = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:testing
        CALSCALE:GREGORIAN
        BEGIN:VEVENT
        CREATED:20220316T121102Z
        LAST-MODIFIED:20230127T151619Z
        DTSTAMP:20230127T151619Z
        UID:something
        SUMMARY:testing@testing.com
        RRULE:FREQ=WEEKLY
        DTSTART;TZID=Europe/Madrid:20220309T130000
        DTEND;TZID=Europe/Madrid:20220309T133000
        END:VEVENT
        BEGIN:VEVENT
        CREATED:20220316T121102Z
        LAST-MODIFIED:20230127T151619Z
        DTSTAMP:20230127T151619Z
        UID:something-else
        SUMMARY:testing_unknown@testing.com
        RRULE:FREQ=WEEKLY
        DTSTART;TZID=Europe/Madrid:20220309T150000
        DTEND;TZID=Europe/Madrid:20220309T153000
        END:VEVENT
        END:VCALENDAR
    """
    )
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        cached_ical_file_primary=cached_ical_primary_schedule,
    )

    url = reverse("api-internal:schedule-next-shifts-per-user", kwargs={"pk": schedule.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK

    assert set(response.data["users"].keys()) == {user.public_primary_key}


@pytest.mark.django_db
def test_related_users(
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
    user_a, user_b, user_c, _ = (make_user_for_organization(organization, username=i) for i in "ABCD")

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 8, 2),  # r1-1: 8-10 / A
        (user_b, 2, 16, 2),  # r2-2: 16-18 / B
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
    schedule.refresh_ical_file()

    url = reverse("api-internal:schedule-related-users", kwargs={"pk": schedule.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK

    expected = [ScheduleUserSerializer(u).data for u in (user_a, user_b, user_c)]
    assert sorted(response.data["users"], key=lambda u: u["username"]) == sorted(expected, key=lambda u: u["username"])


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
    for _ in range(3):
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

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    # tomorrow
    request_date = now + timezone.timedelta(days=1)

    user_a = make_user_for_organization(organization)
    user_b = make_user_for_organization(organization)
    user_c = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

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

    expected_users = {
        "users": sorted([user_a.username, user_b.username]),
        "missing_users": [user_c.username],
    }

    # final schedule
    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=3".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    returned_users = [
        {
            "users": sorted([u["display_name"] for u in e["users"]]) if e["users"] else None,
            "missing_users": e["missing_users"],
        }
        for e in response.data["events"]
        if not e["is_gap"]
    ]
    for users in returned_users:
        assert users == expected_users

    # rotations
    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=3&type=rotation".format(request_date.strftime("%Y-%m-%d"))
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    returned_users = [
        {
            "users": sorted([u["display_name"] for u in e["users"]]) if e["users"] else None,
            "missing_users": e["missing_users"],
        }
        for e in response.data["events"]
        if not e["is_gap"]
    ]
    for users in returned_users:
        assert users == expected_users


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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_filter_shift_swaps_permissions(
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
    url = reverse("api-internal:schedule-filter-shift-swaps", kwargs={"pk": schedule.public_primary_key})

    with patch(
        "apps.api.views.schedule.ScheduleView.filter_shift_swaps",
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_current_user_events_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:schedule-current-user-events")

    with patch(
        "apps.api.views.schedule.ScheduleView.current_user_events",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
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
def test_get_schedule_on_call_now(
    make_organization, make_user_for_organization, make_token_for_organization, make_schedule, make_user_auth_headers
):
    organization = make_organization(grafana_url="https://example.com")
    user = make_user_for_organization(organization, username="test", avatar_url="/avatar/test123")
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    client = APIClient()
    url = reverse("api-internal:schedule-list")
    with patch(
        "apps.api.views.schedule.get_oncall_users_for_multiple_schedules",
        return_value={schedule: [user]},
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["on_call_now"] == [
        {
            "pk": user.public_primary_key,
            "username": "test",
            "avatar": "/avatar/test123",
            "avatar_full": "https://example.com/avatar/test123",
        }
    ]


@pytest.mark.django_db
def test_current_user_events(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization, current_user, token = make_organization_and_user_with_plugin_token()
    other_user = make_user_for_organization(organization)
    client = APIClient()
    url = reverse("api-internal:schedule-current-user-events")

    schedule_with_current_user = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    other_schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    shifts = (
        # schedule, user, priority, start time (h), duration (seconds)
        (other_schedule, other_user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
        (schedule_with_current_user, current_user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for schedule, user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

        schedule.refresh_ical_file()
        schedule.refresh_ical_final_schedule()

    response = client.get(url, format="json", **make_user_auth_headers(current_user, token))
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert result["is_oncall"] is True
    assert len(result["schedules"]) == 1
    assert result["schedules"][0]["id"] == schedule_with_current_user.public_primary_key
    assert result["schedules"][0]["name"] == schedule_with_current_user.name
    assert len(result["schedules"][0]["events"]) > 0
    for event in result["schedules"][0]["events"]:
        # check the current user shift is populated
        assert event["shift"] == {
            "pk": on_call_shift.public_primary_key,
            "name": on_call_shift.name,
            "type": on_call_shift.type,
        }


@pytest.mark.django_db
def test_current_user_events_out_of_range(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, current_user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule_with_current_user = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    shifts = (
        # schedule, user, priority, start time (h), duration (seconds)
        (schedule_with_current_user, current_user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = 3
    start_date = today + timezone.timedelta(days=days)
    for schedule, user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

        schedule.refresh_ical_file()
        schedule.refresh_ical_final_schedule()

    url = reverse("api-internal:schedule-current-user-events") + f"?days={days}"
    response = client.get(url, format="json", **make_user_auth_headers(current_user, token))
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert result["is_oncall"] is False
    assert len(result["schedules"]) == 0


@pytest.mark.django_db
def test_current_user_events_no_schedules(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, current_user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:schedule-current-user-events")
    response = client.get(url, format="json", **make_user_auth_headers(current_user, token))
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert result["is_oncall"] is False
    assert len(result["schedules"]) == 0


@pytest.mark.django_db
def test_current_user_events_multiple_schedules(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization, current_user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:schedule-current-user-events")

    schedule_1 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    schedule_2 = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    shifts = (
        # schedule, user, priority, start time (h), duration (seconds)
        (schedule_1, current_user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
        (schedule_2, current_user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for schedule, user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

        schedule.refresh_ical_file()
        schedule.refresh_ical_final_schedule()

    response = client.get(url, format="json", **make_user_auth_headers(current_user, token))
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert result["is_oncall"] is True
    assert len(result["schedules"]) == 2
    assert result["schedules"][0]["id"] != result["schedules"][1]["id"]
    assert result["schedules"][0]["id"] in (schedule_1.public_primary_key, schedule_2.public_primary_key)
    assert result["schedules"][0]["name"] in (schedule_1.name, schedule_2.name)
    assert result["schedules"][1]["id"] in (schedule_1.public_primary_key, schedule_2.public_primary_key)
    assert result["schedules"][1]["name"] in (schedule_1.name, schedule_2.name)
    assert len(result["schedules"][0]["events"]) > 0
    assert len(result["schedules"][1]["events"]) > 0


@pytest.mark.django_db
def test_team_not_updated_if_not_in_data(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_schedule,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    schedule = make_schedule(organization, team=team, schedule_class=OnCallScheduleWeb)

    assert schedule.team == team

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})
    data = {"name": "renamed", "type": 2}
    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["team"] == schedule.team.public_primary_key

    schedule.refresh_from_db()
    assert schedule.team == team


@patch.object(SlackUserGroup, "can_be_updated", new_callable=PropertyMock)
@pytest.mark.django_db
def test_can_update_user_groups(
    mock_user_group_can_be_updated,
    make_organization_and_user_with_plugin_token,
    make_slack_team_identity,
    make_schedule,
    make_slack_user_group,
    make_user_auth_headers,
):
    mock_user_group_can_be_updated.return_value = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    inactive_user_group = make_slack_user_group(slack_team_identity, is_active=False)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, user_group=inactive_user_group)

    client = APIClient()
    url = reverse("api-internal:schedule-detail", kwargs={"pk": schedule.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["warnings"] == [ScheduleBaseSerializer.CANT_UPDATE_USER_GROUP_WARNING]
    mock_user_group_can_be_updated.assert_not_called()  # should not be called for inactive user group (is_active=False)

    active_user_group = make_slack_user_group(slack_team_identity, is_active=True)
    schedule.user_group = active_user_group
    schedule.save()
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["warnings"] == []
    mock_user_group_can_be_updated.assert_called_once()  # should be called for active user group (is_active=True)
