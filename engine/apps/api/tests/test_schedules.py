import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient

from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)
from common.constants.role import Role

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
def test_get_list_schedules(schedule_internal_api_setup, make_user_auth_headers):
    user, token, calendar_schedule, ical_schedule, web_schedule, slack_channel = schedule_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:schedule-list")

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
        },
    ]
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


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
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_detail_web_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, _, web_schedule, _ = schedule_internal_api_setup
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
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == data


@pytest.mark.django_db
def test_create_invalid_ical_schedule(schedule_internal_api_setup, make_user_auth_headers):
    user, token, _, ical_schedule, _, _ = schedule_internal_api_setup
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

    data = {
        "start": timezone.now().replace(microsecond=0),
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
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "shift_uuid": str(on_call_shift.uuid),
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
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "shift_uuid": str(on_call_shift.uuid),
            },
            {
                "all_day": False,
                "start": fri_start,
                "end": fri_start + on_call_shift.duration,
                "users": [{"display_name": user.username, "pk": user.public_primary_key}],
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "shift_uuid": str(on_call_shift.uuid),
            },
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
def test_filter_events_range_calendar(
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

    mon_start = now - timezone.timedelta(days=start_date.weekday())
    request_date = mon_start + timezone.timedelta(days=2)

    url = reverse("api-internal:schedule-filter-events", kwargs={"pk": schedule.public_primary_key})
    url += "?date={}&days=3".format(request_date.strftime("%Y-%m-%d"))
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
                "priority_level": on_call_shift.priority_level,
                "source": "api",
                "calendar_type": OnCallSchedule.PRIMARY,
                "is_empty": False,
                "is_gap": False,
                "shift_uuid": str(on_call_shift.uuid),
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
    [(Role.ADMIN, status.HTTP_200_OK), (Role.EDITOR, status.HTTP_200_OK), (Role.VIEWER, status.HTTP_200_OK)],
)
def test_schedule_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
    [(Role.ADMIN, status.HTTP_200_OK), (Role.EDITOR, status.HTTP_200_OK), (Role.VIEWER, status.HTTP_200_OK)],
)
def test_schedule_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
        (Role.ADMIN, status.HTTP_204_NO_CONTENT),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_events_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_reload_ical_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_notify_oncall_shift_freq_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    url = reverse("api-internal:schedule-notify-oncall-shift-freq-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_notify_empty_oncall_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    url = reverse("api-internal:schedule-notify-empty-oncall-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_schedule_mention_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    url = reverse("api-internal:schedule-mention-options")
    client = APIClient()
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
