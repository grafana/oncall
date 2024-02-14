from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleWeb

invalid_field_data_1 = {
    "frequency": None,
}

invalid_field_data_2 = {
    "start": timezone.now(),
}

invalid_field_data_3 = {
    "by_day": ["QQ", "FR"],
}

invalid_field_data_4 = {
    "by_month": [13],
}

invalid_field_data_5 = {
    "by_monthday": [35],
}

invalid_field_data_6 = {
    "interval": 0,
}

invalid_field_data_7 = {
    "type": "invalid_type",
}

invalid_field_data_8 = {
    "until": "not-a-date",
}

invalid_field_data_9 = {
    "frequency": CustomOnCallShift.FREQUENCY_DAILY,
    "interval": 5,
}

invalid_field_data_10 = {
    "time_zone": "asdfasdfasdf",
}


@pytest.mark.django_db
def test_filter_on_call_shift_schedule(make_organization_and_user_with_token, make_on_call_shift, make_schedule):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule_1 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    schedule_2 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start_date = timezone.now().replace(microsecond=0)
    shifts = []
    for schedule in (schedule_1, schedule_2):
        data = {
            "start": start_date,
            "rotation_start": start_date,
            "duration": timezone.timedelta(seconds=7200),
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
        )
        on_call_shift.users.add(user)
        shifts.append(on_call_shift)

    url = reverse("api-public:on_call_shifts-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    expected = sorted([s.public_primary_key for s in shifts])
    returned = sorted([s["id"] for s in response.json()["results"]])
    assert returned == expected

    url += f"?schedule_id={schedule_1.public_primary_key}"
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    expected = [shifts[0].public_primary_key]
    returned = [s["id"] for s in response.json()["results"]]
    assert returned == expected


@pytest.mark.django_db
def test_get_on_call_shift(make_organization_and_user_with_token, make_on_call_shift, make_schedule):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
    }
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)
    schedule.custom_on_call_shifts.add(on_call_shift)

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": schedule.public_primary_key,
        "name": on_call_shift.name,
        "type": "single_event",
        "time_zone": None,
        "level": 0,
        "start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": int(on_call_shift.duration.total_seconds()),
        "users": [user.public_primary_key],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == result


@pytest.mark.django_db
def test_get_override_on_call_shift(make_organization_and_user_with_token, make_on_call_shift, make_schedule):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **data)
    on_call_shift.users.add(user)

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": schedule.public_primary_key,
        "name": on_call_shift.name,
        "type": "override",
        "time_zone": None,
        "start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": int(on_call_shift.duration.total_seconds()),
        "users": [user.public_primary_key],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == result


@pytest.mark.django_db
def test_get_web_override_shift(
    make_organization_and_user_with_token, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    start_data = timezone.now().replace(microsecond=0)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    data = {
        "name": "override shift",
        "start": start_data,
        "rotation_start": start_data,
        "duration": timezone.timedelta(hours=9),
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization,
        source=CustomOnCallShift.SOURCE_WEB,
        shift_type=CustomOnCallShift.TYPE_OVERRIDE,
        **data,
    )
    on_call_shift.add_rolling_users([[user]])

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": schedule.public_primary_key,
        "name": on_call_shift.name,
        "type": "override",
        "time_zone": None,
        "start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": int(on_call_shift.duration.total_seconds()),
        "users": list({user.public_primary_key}),
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == result


@pytest.mark.django_db
def test_create_on_call_shift(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    until = start + timezone.timedelta(days=30)
    data = {
        "team_id": None,
        "name": "test name",
        "type": "recurrent_event",
        "level": 1,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
        "week_start": "MO",
        "frequency": "weekly",
        "interval": 2,
        "until": until.strftime("%Y-%m-%dT%H:%M:%S"),
        "by_day": ["MO", "WE", "FR"],
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    on_call_shift = CustomOnCallShift.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": None,
        "name": data["name"],
        "type": "recurrent_event",
        "time_zone": None,
        "level": data["level"],
        "start": data["start"],
        "rotation_start": data["rotation_start"],
        "duration": data["duration"],
        "frequency": data["frequency"],
        "interval": data["interval"],
        "until": data["until"],
        "week_start": data["week_start"],
        "by_day": data["by_day"],
        "users": [user.public_primary_key],
        "by_month": None,
        "by_monthday": None,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == result


@pytest.mark.django_db
def test_create_on_call_shift_using_default_interval(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    until = start + timezone.timedelta(days=30)
    data = {
        "team_id": None,
        "name": "test name",
        "type": "recurrent_event",
        "level": 1,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
        "week_start": "MO",
        "frequency": "weekly",
        "until": until.strftime("%Y-%m-%dT%H:%M:%S"),
        "by_day": ["MO", "WE", "FR"],
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    on_call_shift = CustomOnCallShift.objects.get(public_primary_key=response.data["id"])

    expected = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": None,
        "name": data["name"],
        "type": "recurrent_event",
        "time_zone": None,
        "level": data["level"],
        "start": data["start"],
        "rotation_start": data["rotation_start"],
        "duration": data["duration"],
        "frequency": data["frequency"],
        "interval": 1,
        "until": data["until"],
        "week_start": data["week_start"],
        "by_day": data["by_day"],
        "users": [user.public_primary_key],
        "by_month": None,
        "by_monthday": None,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == expected


@pytest.mark.django_db
def test_create_on_call_shift_using_none_interval_fails(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    until = start + timezone.timedelta(days=30)
    data = {
        "team_id": None,
        "name": "test name",
        "type": "recurrent_event",
        "level": 1,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
        "week_start": "MO",
        "frequency": "weekly",
        "interval": None,
        "until": until.strftime("%Y-%m-%dT%H:%M:%S"),
        "by_day": ["MO", "WE", "FR"],
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Field 'interval' must be a positive integer"}


@pytest.mark.django_db
def test_create_on_call_shift_no_interval_fallback(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    until = start + timezone.timedelta(days=30)
    data = {
        "team_id": None,
        "name": "test name",
        "type": "recurrent_event",
        "level": 1,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
        "frequency": "daily",
        "until": until.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    on_call_shift = CustomOnCallShift.objects.get(public_primary_key=response.data["id"])
    expected = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": None,
        "name": data["name"],
        "type": "recurrent_event",
        "time_zone": None,
        "level": data["level"],
        "start": data["start"],
        "rotation_start": data["rotation_start"],
        "duration": data["duration"],
        "frequency": data["frequency"],
        "interval": 1,
        "until": data["until"],
        "by_day": None,
        "users": [user.public_primary_key],
        "by_month": None,
        "by_monthday": None,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == expected


@pytest.mark.django_db
def test_create_override_on_call_shift(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    data = {
        "team_id": None,
        "name": "test name",
        "type": "override",
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    on_call_shift = CustomOnCallShift.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": None,
        "name": data["name"],
        "type": "override",
        "time_zone": None,
        "start": data["start"],
        "rotation_start": data["rotation_start"],
        "duration": data["duration"],
        "users": [user.public_primary_key],
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == result


@pytest.mark.django_db
def test_create_on_call_shift_invalid_time_zone(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now()
    until = start + timezone.timedelta(days=30)
    data = {
        "team_id": None,
        "name": "test name",
        "type": "recurrent_event",
        "level": 1,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": 10800,
        "users": [user.public_primary_key],
        "week_start": "MO",
        "frequency": "weekly",
        "interval": 2,
        "until": until.strftime("%Y-%m-%dT%H:%M:%S"),
        "by_day": ["MO", "WE", "FR"],
        "time_zone": "asdfasdfasdf",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"time_zone": ["Invalid timezone"]}


@pytest.mark.django_db
def test_update_on_call_shift(make_organization_and_user_with_token, make_on_call_shift, make_schedule):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "interval": 2,
        "by_day": ["MO", "FR"],
    }

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )
    schedule.custom_on_call_shifts.add(on_call_shift)

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    data_to_update = {
        "duration": 14400,
        "users": [user.public_primary_key],
        "by_day": ["MO", "WE", "FR"],
    }

    assert int(on_call_shift.duration.total_seconds()) != data_to_update["duration"]
    assert on_call_shift.by_day != data_to_update["by_day"]
    assert len(on_call_shift.users.filter(public_primary_key=user.public_primary_key)) == 0

    with patch("apps.schedules.models.CustomOnCallShift.start_drop_ical_and_check_schedule_tasks") as mock_drop_ical:
        response = client.put(url, data=data_to_update, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": schedule.public_primary_key,
        "name": on_call_shift.name,
        "type": "recurrent_event",
        "time_zone": None,
        "level": 0,
        "start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": on_call_shift.rotation_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": data_to_update["duration"],
        "frequency": "weekly",
        "interval": on_call_shift.interval,
        "until": None,
        "week_start": "SU",
        "by_day": data_to_update["by_day"],
        "users": [user.public_primary_key],
        "by_month": None,
        "by_monthday": None,
    }

    assert response.status_code == status.HTTP_200_OK
    on_call_shift.refresh_from_db()

    assert int(on_call_shift.duration.total_seconds()) == data_to_update["duration"]
    assert on_call_shift.by_day == data_to_update["by_day"]
    assert len(on_call_shift.users.filter(public_primary_key=user.public_primary_key)) == 1
    assert response.data == result
    mock_drop_ical.assert_called_once_with(schedule)


@pytest.mark.django_db
def test_update_on_call_shift_web_schedule(make_organization_and_user_with_token, make_on_call_shift, make_schedule):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "interval": 2,
        "by_day": ["MO", "FR"],
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})
    data_to_update = {
        "duration": 14400,
        "by_day": ["MO", "WE", "FR"],
    }
    assert int(on_call_shift.duration.total_seconds()) != data_to_update["duration"]
    assert on_call_shift.by_day != data_to_update["by_day"]

    with patch("apps.schedules.models.CustomOnCallShift.start_drop_ical_and_check_schedule_tasks") as mock_drop_ical:
        response = client.put(url, data=data_to_update, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": on_call_shift.public_primary_key,
        "team_id": None,
        "schedule": schedule.public_primary_key,
        "name": on_call_shift.name,
        "type": "rolling_users",
        "time_zone": None,
        "level": 0,
        "start": on_call_shift.start.strftime("%Y-%m-%dT%H:%M:%S"),
        "rotation_start": on_call_shift.rotation_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": data_to_update["duration"],
        "frequency": "weekly",
        "interval": on_call_shift.interval,
        "until": None,
        "week_start": "SU",
        "by_day": data_to_update["by_day"],
        "rolling_users": [[user.public_primary_key]],
        "start_rotation_from_user_index": None,
        "by_month": None,
        "by_monthday": None,
    }

    assert response.status_code == status.HTTP_200_OK
    on_call_shift.refresh_from_db()
    assert int(on_call_shift.duration.total_seconds()) == data_to_update["duration"]
    assert on_call_shift.by_day == data_to_update["by_day"]
    assert response.data == result
    mock_drop_ical.assert_called_once_with(schedule)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_to_update",
    [
        invalid_field_data_1,
        invalid_field_data_2,
        invalid_field_data_3,
        invalid_field_data_4,
        invalid_field_data_5,
        invalid_field_data_6,
        invalid_field_data_7,
        invalid_field_data_8,
        invalid_field_data_9,
        invalid_field_data_10,
    ],
)
def test_update_on_call_shift_invalid_field(make_organization_and_user_with_token, make_on_call_shift, data_to_update):
    organization, _, token = make_organization_and_user_with_token()
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "interval": 2,
        "by_day": ["MO", "FR"],
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.put(url, data=data_to_update, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_delete_on_call_shift(make_organization_and_user_with_token, make_on_call_shift):
    organization, _, token = make_organization_and_user_with_token()
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": on_call_shift.public_primary_key})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(CustomOnCallShift.DoesNotExist):
        on_call_shift.refresh_from_db()


@pytest.mark.django_db
def test_create_web_override(make_organization_and_user_with_token, make_on_call_shift):
    _, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:on_call_shifts-list")

    start = timezone.now().replace(microsecond=0)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    data = {
        "team_id": None,
        "name": "test web override",
        "type": "override",
        "source": 0,
        "start": start_str,
        "duration": 3600,
        "users": [user.public_primary_key],
        "time_zone": "UTC",
    }
    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    shift = CustomOnCallShift.objects.get(name="test web override")
    expected_response = {
        "id": shift.public_primary_key,
        "team_id": None,
        "schedule": None,
        "name": "test web override",
        "type": "override",
        "start": start_str,
        "rotation_start": start_str,
        "duration": 3600,
        "users": [user.public_primary_key],
        "time_zone": "UTC",
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response

    assert shift.rolling_users == [{str(user.pk): user.public_primary_key}]
    assert shift.priority_level == 99
    assert shift.start == start
    assert shift.rotation_start == start
