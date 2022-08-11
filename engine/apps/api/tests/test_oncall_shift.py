from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from common.constants.role import Role


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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "title": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": 1,
        "interval": None,
        "by_day": [
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY],
            CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.FRIDAY],
        ],
        "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))
    expected_payload = data | {"id": response.data["id"], "updated_shift": None}

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_create_on_call_shift_override(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "title": "Test Shift Override",
        "type": CustomOnCallShift.TYPE_OVERRIDE,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
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
    expected_payload = data | {"id": response.data["id"], "updated_shift": None}

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = timezone.now().replace(microsecond=0)

    title = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}, {user2.pk: user2.public_primary_key}],
    )
    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user1, token))
    expected_payload = {
        "id": response.data["id"],
        "title": title,
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = timezone.now().replace(microsecond=0)
    title = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
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
                "title": title,
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
                "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
                "updated_shift": None,
            }
        ],
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
    title = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
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
                "title": title,
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
                "rolling_users": [[user1.public_primary_key], [user2.public_primary_key]],
                "updated_shift": None,
            }
        ],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    expected_payload = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() + timezone.timedelta(days=1)).replace(microsecond=0)

    title = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "title": title,
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
        "title": title,
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
        "rolling_users": [[user1.public_primary_key]],
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    on_call_shift.refresh_from_db()
    assert on_call_shift.priority_level == data_to_update["priority_level"]


@pytest.mark.django_db
def test_update_started_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the shift that has started (rotation_start < now)"""

    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    title = "Test Shift Rotation"
    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    data_to_update = {
        "title": title,
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
        "id": response.data["id"],
        "title": title,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": response.data["rotation_start"],
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
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


@pytest.mark.django_db
def test_update_old_on_call_shift_with_future_version(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the shift that has the newer version (updated_shift is not None)"""
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(days=3)).replace(microsecond=0)
    next_rotation_start_date = start_date + timezone.timedelta(days=5)
    updated_duration = timezone.timedelta(hours=4)

    title = "Test Shift Rotation"
    new_on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=next_rotation_start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
    )
    old_on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=3),
        rotation_start=start_date,
        until=next_rotation_start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
        updated_shift=new_on_call_shift,
    )
    # update shift_end and priority_level
    data_to_update = {
        "title": title,
        "priority_level": 2,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + updated_duration).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": next_rotation_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    assert old_on_call_shift.duration != updated_duration
    assert old_on_call_shift.priority_level != data_to_update["priority_level"]
    assert new_on_call_shift.duration != updated_duration
    assert new_on_call_shift.priority_level != data_to_update["priority_level"]

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": old_on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    expected_payload = data_to_update | {
        "id": new_on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    new_on_call_shift.refresh_from_db()
    # check if the newest version of shift was changed
    assert old_on_call_shift.duration != updated_duration
    assert old_on_call_shift.priority_level != data_to_update["priority_level"]
    assert new_on_call_shift.duration == updated_duration
    assert new_on_call_shift.priority_level == data_to_update["priority_level"]


@pytest.mark.django_db
def test_update_started_on_call_shift_title(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test updating the title for the shift that has started (rotation_start < now)"""

    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    title = "Test Shift Rotation"
    new_title = "Test Shift Rotation RENAMED"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
        start=start_date,
        duration=timezone.timedelta(hours=1),
        rotation_start=start_date,
        rolling_users=[{user1.pk: user1.public_primary_key}],
        source=CustomOnCallShift.SOURCE_WEB,
        week_start=CustomOnCallShift.MONDAY,
    )
    # update only title
    data_to_update = {
        "title": new_title,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": None,
        "interval": None,
        "by_day": None,
        "rolling_users": [[user1.public_primary_key]],
    }

    assert on_call_shift.title != new_title

    url = reverse("api-internal:oncall_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user1, token))

    expected_payload = data_to_update | {
        "id": on_call_shift.public_primary_key,
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "updated_shift": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload

    on_call_shift.refresh_from_db()
    assert on_call_shift.title == new_title


@pytest.mark.django_db
def test_delete_started_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test deleting the shift that has started (rotation_start < now)"""

    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() - timezone.timedelta(hours=1)).replace(microsecond=0)

    title = "Test Shift Rotation"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
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
def test_delete_future_on_call_shift(
    on_call_shift_internal_api_setup,
    make_on_call_shift,
    make_user_auth_headers,
):
    """Test deleting the shift that has not started (rotation_start > now)"""

    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup

    client = APIClient()
    start_date = (timezone.now() + timezone.timedelta(days=1)).replace(microsecond=0)

    title = "Test Shift Rotation"

    on_call_shift = make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        title=title,
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # rotation_start < shift_start
    data = {
        "title": "Test Shift 1",
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # until < rotation_start
    data = {
        "title": "Test Shift",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 1,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": (start_date - timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frequency": 1,
        "interval": None,
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
        "title": "Test Shift 2",
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # by_day with non-recurrent shift
    data = {
        "title": "Test Shift 1",
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

    # by_day with non-weekly frequency
    data = {
        "title": "Test Shift 2",
        "type": CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        "schedule": schedule.public_primary_key,
        "priority_level": 0,
        "shift_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shift_end": (start_date + timezone.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": None,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": None,
        "by_day": [CustomOnCallShift.ICAL_WEEKDAY_MAP[CustomOnCallShift.MONDAY]],
        "rolling_users": [[user1.public_primary_key]],
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user1, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["by_day"][0] == "Cannot set days value for this frequency type"


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_interval(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # interval with non-recurrent shift
    data = {
        "title": "Test Shift 2",
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


@pytest.mark.django_db
def test_create_on_call_shift_invalid_data_shift_end(on_call_shift_internal_api_setup, make_user_auth_headers):
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # shift_end is None
    data = {
        "title": "Test Shift 1",
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
        "title": "Test Shift 2",
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    data = {
        "title": "Test Shift 1",
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
    token, user1, user2, organization, schedule = on_call_shift_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:oncall_shifts-list")
    start_date = timezone.now().replace(microsecond=0, tzinfo=None)

    # override shift with frequency
    data = {
        "title": "Test Shift Override",
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
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_201_CREATED),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_on_call_shift_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_on_call_shift_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
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
        (Role.ADMIN, status.HTTP_204_NO_CONTENT),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
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
