from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import CustomOnCallShift, OnCallSchedule, OnCallScheduleCalendar, OnCallScheduleWeb


@pytest.fixture()
def on_call_shift_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_user_for_organization,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    return token, first_user, second_user, organization, schedule


@pytest.mark.django_db
def test_create_on_call_shift_rotation(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "name": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": 1,
        "by_day": [
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.FRIDAY],
        ],
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
        "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
    }

    with patch("apps.schedules.models.CustomOnCallShift.refresh_schedule") as mock_refresh_schedule:
        response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    expected_payload = data | {"id": response.data["id"], "updated_shift": None}
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_payload
    assert mock_refresh_schedule.called


@pytest.mark.django_db
def test_create_on_call_shift_rotation_invalid_type(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)

    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "name": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": 1,
        "by_day": [
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.FRIDAY],
        ],
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
        "rolling_users": [[user.public_primary_key]],
    }

    with patch("apps.schedules.models.CustomOnCallShift.refresh_schedule") as mock_refresh_schedule:
        response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["type"][0] == "Invalid event type"
    assert not mock_refresh_schedule.called


@pytest.mark.django_db
def test_create_on_call_shift_rotation_missing_users(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "name": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": 1,
        "by_day": [
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.FRIDAY],
        ],
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
        "rolling_users": [],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["rolling_users"][0] == "User(s) are required"


@pytest.mark.django_db
def test_create_on_call_shift_override(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "name": "Test Shift Override",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 99,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key, user2.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))
    returned_rolling_users = response.data["rolling_users"]
    assert len(returned_rolling_users) == 1
    assert sorted(returned_rolling_users[0]) == sorted(data["rolling_users"][0])
    expected_payload = data | {
        "id": response.data["id"],
        "updated_shift": None,
        "rolling_users": returned_rolling_users,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = timezone.now().replace(microsecond=0)

    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}, {user2.pk: user2.public_primary_key}],
    )
    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user1, token))
    expected_payload = {
        "id": response.data["id"],
        "name": name,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.SUNDAY],
        "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_list_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = timezone.now().replace(microsecond=0)
    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}, {user2.pk: user2.public_primary_key}],
    )
    url = reverse("api-internal:oncall_shifts-list")

    response = client.get(url, format="json", **make_user_auth_headers(user1, token))
    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": on_call_shift.public_primary_key,
                "name": name,
                "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
                "schedule": schedule.public_primary_key,
                "priority_level": 0,
                "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "until": None,
                "frequency": None,
                "interval": None,
                "by_day": None,
                "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.SUNDAY],
                "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
                "updated_shift": None,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_list_on_call_shift_filter_schedule_id(
    on_call_shift_internal_api_setup,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    schedule_without_shifts = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}, {user2.pk: user2.public_primary_key}],
    )
    url = reverse("api-internal:oncall_shifts-list")

    response = client.get(
        url + f"?schedule_id={schedule.public_primary_key}", format="json", **make_user_auth_headers(user1, token)
    )
    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": on_call_shift.public_primary_key,
                "name": name,
                "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
                "schedule": schedule.public_primary_key,
                "priority_level": 0,
                "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "until": None,
                "frequency": None,
                "interval": None,
                "by_day": None,
                "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.SUNDAY],
                "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
                "updated_shift": None,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    expected_payload = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    response = client.get(
        url + f"?schedule_id={schedule_without_shifts.public_primary_key}",
        format="json",
        **make_user_auth_headers(user1, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_update_future_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the shift that has not started (rotation_start > now)"""
    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() + timezone.timedelta(days=1)).replace(microsecond=0)

    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "name": name,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    assert on_call_shift.priority_level != data_to_update["priority_level"]

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    expected_payload = {
        "id": on_call_shift.public_primary_key,
        "name": name,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
        "rolling_users": [[user1.public_primary_key]],
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    on_call_shift.refresh_from_db()
    assert on_call_shift.priority_level == data_to_update["priority_level"]


@pytest.mark.django_db
def test_update_future_on_call_shift_removing_users(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() + timezone.timedelta(days=1)).replace(microsecond=0)

    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "name": name,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [],
    }

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})
    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["rolling_users"][0] == "User(s) are required"


@pytest.mark.django_db
def test_update_started_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the shift that has started (rotation_start < now)"""

    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "name": name,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    assert on_call_shift.priority_level != data_to_update["priority_level"]

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    with patch("apps.schedules.models.CustomOnCallShift.refresh_schedule") as mock_refresh_schedule:
        response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    expected_payload = {
        "id": response.data["id"],
        "name": name,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": response.data["rotation_start"],
        "until": None,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
        "by_day": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
        "rolling_users": [[user1.public_primary_key]],
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    # check that another shift was created
    assert response.data["id"] != on_call_shift.public_primary_key
    on_call_shift.refresh_from_db()
    assert on_call_shift.priority_level != data_to_update["priority_level"]
    assert on_call_shift.updated_shift.public_primary_key == response.data["id"]
    # check if until date was changed
    assert on_call_shift.until is not None
    assert on_call_shift.until == on_call_shift.updated_shift.rotation_start
    assert mock_refresh_schedule.called


@pytest.mark.django_db
def test_update_started_on_call_shift_force_update(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    name = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "name": name,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.SUNDAY],
        "rolling_users": [[user1.public_primary_key]],
    }

    assert on_call_shift.priority_level != data_to_update["priority_level"]

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key}) + "?force=true"

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_200_OK
    # check no shift was created
    assert response.data["id"] == on_call_shift.public_primary_key
    on_call_shift.refresh_from_db()
    assert on_call_shift.priority_level == data_to_update["priority_level"]
    assert on_call_shift.updated_shift is None
    assert on_call_shift.until is None


@pytest.mark.django_db
def test_update_old_on_call_shift_with_future_version(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the shift that has the newer version (updated_shift is not None)"""
    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=3)
    next_rotation_start_date = now + timezone.timedelta(days=1)
    updated_duration = timezone.timedelta(hours=4)

    name = "Test Shift Rotation"
    new_on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=next_rotation_start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=next_rotation_start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
    )
    old_on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=start_date,
        until=next_rotation_start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
        updated_shift=new_on_call_shift,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
    )
    # update shift_end and priority_level
    data_to_update = {
        "name": name,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + updated_duration).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    assert old_on_call_shift.duration != updated_duration
    assert old_on_call_shift.priority_level != data_to_update["priority_level"]
    assert new_on_call_shift.duration != updated_duration
    assert new_on_call_shift.priority_level != data_to_update["priority_level"]

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": old_on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))
    response_data = response.json()

    for key in ["shift_start", "shift_end", "rotation_start"]:
        data_to_update.pop(key)
        response_data.pop(key)

    expected_payload = data_to_update | {
        "id": new_on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "updated_shift": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    assert old_on_call_shift.duration != updated_duration
    assert old_on_call_shift.priority_level != data_to_update["priority_level"]
    new_on_call_shift.refresh_from_db()
    # check if the newest version of shift was changed
    assert new_on_call_shift.start - now < timezone.timedelta(minutes=1)
    assert new_on_call_shift.rotation_start - now < timezone.timedelta(minutes=1)
    assert new_on_call_shift.duration == updated_duration
    assert new_on_call_shift.priority_level == data_to_update["priority_level"]


@pytest.mark.django_db
def test_update_started_on_call_shift_name(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the name for the shift that has started (rotation_start < now)"""

    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    name = "Test Shift Rotation"
    new_name = "Test Shift Rotation RENAMED"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
        source=CustomOnCallShift.SOURCE_WEB,
        week_start=CustomOnCallShift.MONDAY,
    )
    # update only name
    data_to_update = {
        "name": new_name,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "week_start": "MO",
        "rolling_users": [[user1.public_primary_key]],
    }

    assert on_call_shift.name != new_name

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    expected_payload = data_to_update | {
        "id": on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "updated_shift": None,
        "week_start": CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    on_call_shift.refresh_from_db()
    assert on_call_shift.name == new_name


@pytest.mark.django_db
def test_delete_started_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test deleting the shift that has started (rotation_start < now)"""

    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    name = "Test Shift Rotation"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    assert on_call_shift.until is None

    response = client.delete(url, **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_204_NO_CONTENT

    on_call_shift.refresh_from_db()
    assert on_call_shift.until is not None


@pytest.mark.django_db
def test_force_delete_started_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test deleting the shift that has started (rotation_start < now)"""

    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    name = "Test Shift Rotation"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )

    # set force=true to hard delete the shift
    url = "{}?force=true".format(
        reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})
    )

    response = client.delete(url, **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(CustomOnCallShift.DoesNotExist):
        on_call_shift.refresh_from_db()


@pytest.mark.django_db
def test_delete_future_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test deleting the shift that has not started (rotation_start > now)"""

    token, user1, _, _, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() + timezone.timedelta(days=1)).replace(microsecond=0)

    name = "Test Shift Rotation"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        name=name,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.delete(url, **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(CustomOnCallShift.DoesNotExist):
        on_call_shift.refresh_from_db()


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_rotation_start(
    on_call_shift_internal_api_setup,
    make_user_auth_headers,
):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # rotation_start < shift_start
    data = {
        "name": "Test Shift 1",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": (start_date - timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["rotation_start"][0] == "Incorrect rotation start date"


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_until(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # until < rotation_start
    data = {
        "name": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": (start_date - timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frequency": 1,
        "interval": 1,
        "by_day": [
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.FRIDAY],
        ],
        "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["until"][0] == "Incorrect rotation end date"

    # until with non-recurrent shift
    data = {
        "name": "Test Shift 2",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["until"][0] == "Cannot set 'until' for non-recurrent shifts"


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_by_day(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # by_day with non-recurrent shift
    data = {
        "name": "Test Shift 1",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": [CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY]],
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["by_day"][0] == "Cannot set days value for non-recurrent shifts"


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_interval(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # interval with non-recurrent shift
    data = {
        "name": "Test Shift 2",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": 2,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["interval"][0] == "Cannot set interval for non-recurrent shifts"

    invalid_intervals = (
        (None, "If frequency is set, interval must be a positive integer"),
        (2, "Interval must be less than or equal to the number of selected days"),
    )
    for interval, expected_error in invalid_intervals:
        # by_day, daily shift
        data = {
            "name": "Test Shift 2",
            "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
            "schedule": schedule.public_primary_key,
            "priority_level": 0,
            "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "until": None,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "by_day": [CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY]],
            "rolling_users": [[user1.public_primary_key]],
        }
        if interval:
            data["interval"] = interval

        response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["interval"][0] == expected_error


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_shift_end(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # shift_end is None
    data = {
        "name": "Test Shift 1",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": None,
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["shift_end"][0] == "This field is required."

    # shift_end < shift_start
    data = {
        "name": "Test Shift 2",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date - timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["shift_end"][0] == "Incorrect shift end date"


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_rolling_users(
    on_call_shift_internal_api_setup,
    make_user_auth_headers,
):
    token, user1, user2, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "name": "Test Shift 1",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["rolling_users"][0] == "Cannot set multiple user groups for non-recurrent shifts"


@pytest.mark.django_db
def test_create_on_call_shift_override_invalid_data(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # override shift with frequency
    data = {
        "name": "Test Shift Override",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["frequency"][0] == "Cannot set 'frequency' for shifts with type 'override'"


@pytest.mark.django_db
def test_create_on_call_shift_override_in_past(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, _, _, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None) - timezone.timedelta(hours=2)

    data = {
        "name": "Test Shift Override",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["shift_end"][0] == "Cannot create or update an override in the past"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.EDITOR, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_on_call_shift_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()

    url = reverse("api-internal:oncall_shifts-list")

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.create",
        return_value=Response(
            status=status.HTTP_201_CREATED,
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
def test_on_call_shift_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start_date = timezone.now()
    on_call_shift = make_on_call_shift(
        organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
    )
    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.update",
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
def test_on_call_shift_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:oncall_shifts-list")

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.list",
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
def test_on_call_shift_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start_date = timezone.now()
    on_call_shift = make_on_call_shift(
        organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
    )
    client = APIClient()

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.retrieve",
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
def test_on_call_shift_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start_date = timezone.now()
    on_call_shift = make_on_call_shift(
        organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
    )
    client = APIClient()

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.destroy",
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
def test_on_call_shift_frequency_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:oncall_shifts-frequency-options")

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.frequency_options",
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
def test_on_call_shift_days_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:oncall_shifts-days-options")

    with patch(
        "apps.api.views.on_call_shifts.OnCallShiftView.days_options",
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
def test_on_call_shift_preview_permissions(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start_date = timezone.now()
    client = APIClient()

    shift_start = (start_date + timezone.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[user.public_primary_key]],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }

    url = reverse("api-internal:oncall_shifts-preview")
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_on_call_shift_preview_missing_data(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    client = APIClient()

    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rolling_users": [[user.public_primary_key]],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }

    url = reverse("api-internal:oncall_shifts-preview")
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_on_call_shift_preview(
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

    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    data = {
        "start": start_date + timezone.timedelta(hours=9),
        "rotation_start": start_date + timezone.timedelta(hours=9),
        "duration": timezone.timedelta(hours=9),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    url = "{}?date={}&days={}".format(
        reverse("api-internal:oncall_shifts-preview"), request_date.strftime("%Y-%m-%d"), 1
    )
    shift_start = (start_date + timezone.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[other_user.public_primary_key]],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # check rotation events
    rotation_events = response.json()["rotation"]
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": shift_start,
            "end": shift_end,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": 2,
            "missing_users": [],
            "users": [
                {
                    "display_name": other_user.username,
                    "pk": other_user.public_primary_key,
                    "email": other_user.email,
                    "avatar_full": other_user.avatar_full_url,
                },
            ],
            "source": "web",
        }
    ]
    # there isn't a saved shift, we don't care/know the temp pk
    _ = [r.pop("shift") for r in rotation_events]
    assert rotation_events == expected_rotation_events

    # check final schedule events
    final_events = response.json()["final"]
    expected = (
        # start (h), duration (H), user, priority
        (9, 3, user.username, 1),  # 9-12 user
        (12, 1, other_user.username, 2),  # 12-13 other_user
        (13, 5, user.username, 1),  # 13-18 C
    )
    expected_events = [
        {
            "end": (start_date + timezone.timedelta(hours=start + duration)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "priority_level": priority,
            "start": (start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_on_call_shift_preview_invalid_type(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    request_date = start_date

    url = "{}?date={}&days={}".format(
        reverse("api-internal:oncall_shifts-preview"), request_date.strftime("%Y-%m-%d"), 1
    )
    shift_start = (start_date + timezone.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[user.public_primary_key]],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["type"][0] == "Invalid event type"


@pytest.mark.django_db
def test_on_call_shift_preview_without_users(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
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

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    request_date = start_date
    user = make_user_for_organization(organization)

    url = "{}?date={}&days={}".format(
        reverse("api-internal:oncall_shifts-preview"), request_date.strftime("%Y-%m-%d"), 1
    )
    shift_start = (start_date + timezone.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        # passing empty users
        "rolling_users": [],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # check rotation events
    rotation_events = response.json()["rotation"]
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": shift_start,
            "end": shift_end,
            "all_day": False,
            "is_override": False,
            "is_empty": True,
            "is_gap": False,
            "priority_level": None,
            "missing_users": [],
            "users": [],
            "source": "web",
        }
    ]
    # there isn't a saved shift, we don't care/know the temp pk
    _ = [r.pop("shift") for r in rotation_events]
    assert rotation_events == expected_rotation_events

    # check final schedule events
    final_events = response.json()["final"]
    expected_events = []
    returned_events = [
        {
            "end": e["end"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
            "is_empty": e["is_empty"],
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_on_call_shift_preview_merge_events(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
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

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    request_date = start_date

    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    url = "{}?date={}&days={}".format(
        reverse("api-internal:oncall_shifts-preview"), request_date.strftime("%Y-%m-%d"), 1
    )
    shift_start = (start_date + timezone.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[user.public_primary_key, other_user.public_primary_key]],
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # check rotation events
    rotation_events = response.json()["rotation"]
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": shift_start,
            "end": shift_end,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": 2,
            "missing_users": [],
            "source": "web",
        }
    ]
    expected_users = sorted([user.username, other_user.username])
    returned_event = rotation_events[0]
    # there isn't a saved shift, we don't care/know the temp pk
    returned_event.pop("shift")
    returned_users = sorted(u["display_name"] for u in returned_event.pop("users"))
    assert sorted(returned_users) == expected_users
    assert rotation_events == expected_rotation_events

    # check final schedule events
    final_events = response.json()["final"]
    expected = (
        # start (h), duration (H), users, priority
        (12, 1, expected_users, 2),  # 12-13 other_user
    )
    expected_events = [
        {
            "end": (start_date + timezone.timedelta(hours=start + duration)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "priority_level": priority,
            "start": (start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "users": users,
        }
        for start, duration, users, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "users": sorted(u["display_name"] for u in e["users"]),
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_on_call_shift_preview_update(
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
    tomorrow = now + timezone.timedelta(days=1)

    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    data = {
        "start": start_date + timezone.timedelta(hours=8),
        "rotation_start": start_date + timezone.timedelta(hours=8),
        "duration": timezone.timedelta(hours=1),
        "priority_level": 1,
        "interval": 4,
        "frequency": CustomOnCallShift.FREQUENCY_HOURLY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    url = "{}?date={}&days={}".format(reverse("api-internal:oncall_shifts-preview"), tomorrow.strftime("%Y-%m-%d"), 1)
    shift_start = (tomorrow + timezone.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (tomorrow + timezone.timedelta(hours=18)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "shift_pk": on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[other_user.public_primary_key]],
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # check rotation events
    rotation_events = response.json()["rotation"]
    assert len(rotation_events) == 1
    # previewing an update reuse shift PK if rotation already started
    new_shift_pk = rotation_events[-1]["shift"]["pk"]
    assert new_shift_pk == on_call_shift.public_primary_key
    expected_shift_preview = {
        "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
        "shift": {"pk": new_shift_pk},
        "start": shift_start,
        "end": shift_end,
        "all_day": False,
        "is_override": False,
        "is_empty": False,
        "is_gap": False,
        "priority_level": 1,
        "missing_users": [],
        "users": [
            {
                "display_name": other_user.username,
                "pk": other_user.public_primary_key,
                "email": other_user.email,
                "avatar_full": other_user.avatar_full_url,
            },
        ],
        "source": "web",
    }
    assert rotation_events[-1] == expected_shift_preview

    # check final schedule events
    final_events = response.json()["final"]
    expected = (
        # start (h), duration (H), user, priority
        (10, 8, other_user.username, 1),  # 10-18 other_user
    )
    expected_events = [
        {
            "end": (tomorrow + timezone.timedelta(hours=start + duration)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "priority_level": priority,
            "start": (tomorrow + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_on_call_shift_preview_update_not_started_reuse_pk(
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
    start_date = now + timezone.timedelta(days=7)
    request_date = start_date

    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    data = {
        "start": start_date + timezone.timedelta(hours=8),
        "rotation_start": start_date + timezone.timedelta(hours=8),
        "duration": timezone.timedelta(hours=1),
        "priority_level": 1,
        "interval": 4,
        "frequency": CustomOnCallShift.FREQUENCY_HOURLY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    url = "{}?date={}&days={}".format(
        reverse("api-internal:oncall_shifts-preview"), request_date.strftime("%Y-%m-%d"), 1
    )
    shift_start = (start_date + timezone.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end = (start_date + timezone.timedelta(hours=18)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_data = {
        "schedule": schedule.public_primary_key,
        "shift_pk": on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "rotation_start": shift_start,
        "shift_start": shift_start,
        "shift_end": shift_end,
        "rolling_users": [[other_user.public_primary_key]],
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 1,
    }
    response = client.post(url, shift_data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # check rotation events
    rotation_events = response.json()["rotation"]
    # previewing an update reuses shift PK when rotation is not started
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "shift": {"pk": on_call_shift.public_primary_key},
            "start": shift_start,
            "end": shift_end,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": 1,
            "missing_users": [],
            "users": [
                {
                    "display_name": other_user.username,
                    "pk": other_user.public_primary_key,
                    "email": other_user.email,
                    "avatar_full": other_user.avatar_full_url,
                },
            ],
            "source": "web",
        },
    ]
    assert rotation_events == expected_rotation_events

    # check final schedule events
    final_events = response.json()["final"]
    expected = (
        # start (h), duration (H), user, priority
        (6, 12, other_user.username, 1),  # 6-18 other_user
    )
    expected_events = [
        {
            "end": (start_date + timezone.timedelta(hours=start + duration)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "priority_level": priority,
            "start": (start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events
