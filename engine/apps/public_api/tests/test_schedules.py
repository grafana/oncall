import collections
import textwrap
from unittest.mock import patch

import pytest
import pytz
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)

ICAL_URL = "https://some.calendar.url"


def assert_expected_shifts_export_response(response, users, expected_on_call_times):
    """Check expected response data for schedule shifts export call."""
    response_json = response.json()
    shifts = response_json["results"]

    total_time_on_call = collections.defaultdict(int)
    pk_to_user_mapping = {
        u.public_primary_key: {
            "email": u.email,
            "username": u.username,
        }
        for u in users
    }

    for row in shifts:
        user_pk = row["user_pk"]

        # make sure we're exporting email and username as well
        assert pk_to_user_mapping[user_pk]["email"] == row["user_email"]
        assert pk_to_user_mapping[user_pk]["username"] == row["user_username"]

        end = timezone.datetime.fromisoformat(row["shift_end"])
        start = timezone.datetime.fromisoformat(row["shift_start"])
        shift_time_in_seconds = (end - start).total_seconds()
        total_time_on_call[row["user_pk"]] += shift_time_in_seconds / (60 * 60)

    for u_pk, on_call_hours in total_time_on_call.items():
        assert on_call_hours == expected_on_call_times[u_pk]

    # pagination parameters are mocked out for now
    del response_json["results"]
    assert response_json == {
        "next": None,
        "previous": None,
        "count": len(shifts),
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }


@pytest.mark.django_db
def test_get_calendar_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        channel=slack_channel_id,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "calendar",
        "time_zone": "UTC",
        "on_call_now": [],
        "shifts": [],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
        "ical_url_overrides": None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result


@pytest.mark.django_db
def test_create_calendar_schedule(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")

    data = {
        "team_id": None,
        "name": "schedule test name",
        "time_zone": "Europe/Moscow",
        "type": "calendar",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "calendar",
        "time_zone": "Europe/Moscow",
        "on_call_now": [],
        "shifts": [],
        "slack": {
            "channel_id": None,
            "user_group_id": None,
        },
        "ical_url_overrides": None,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == result


@pytest.mark.django_db
def test_create_calendar_schedule_with_shifts(make_organization_and_user_with_token, make_team, make_on_call_shift):
    organization, user, token = make_organization_and_user_with_token()
    team = make_team(organization)
    # request user must belong to the team
    team.users.add(user)
    client = APIClient()

    start_date = timezone.now().replace(microsecond=0)
    data = {
        "team": team,
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )

    url = reverse("api-public:schedules-list")
    data = {
        "team_id": team.public_primary_key,
        "name": "schedule test name",
        "time_zone": "Europe/Moscow",
        "type": "calendar",
        "shifts": [on_call_shift.public_primary_key],
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": schedule.public_primary_key,
        "team_id": team.public_primary_key,
        "name": schedule.name,
        "type": "calendar",
        "time_zone": "Europe/Moscow",
        "on_call_now": [],
        "shifts": [on_call_shift.public_primary_key],
        "slack": {
            "channel_id": None,
            "user_group_id": None,
        },
        "ical_url_overrides": None,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == result


@pytest.mark.django_db
def test_update_calendar_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        channel=slack_channel_id,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "name": "RENAMED",
        "time_zone": "Europe/Moscow",
    }

    assert schedule.name != data["name"]
    assert schedule.time_zone != data["time_zone"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": data["name"],
        "type": "calendar",
        "time_zone": data["time_zone"],
        "on_call_now": [],
        "shifts": [],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
        "ical_url_overrides": None,
    }

    assert response.status_code == status.HTTP_200_OK
    schedule.refresh_from_db()
    assert schedule.name == data["name"]
    assert schedule.time_zone == data["time_zone"]
    assert response.json() == result


@pytest.mark.django_db
def test_get_web_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        channel=slack_channel_id,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "web",
        "time_zone": "UTC",
        "on_call_now": [],
        "shifts": [],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result


@pytest.mark.django_db
def test_create_schedules_same_name(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")

    data = {
        "team_id": None,
        "name": "same-name",
        "type": "web",
        "time_zone": "UTC",
    }

    for i in range(2):
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
        assert response.status_code == status.HTTP_201_CREATED

    schedules = OnCallSchedule.objects.filter(name="same-name", organization=organization)
    assert schedules.count() == 2


@pytest.mark.django_db
def test_update_web_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        channel=slack_channel_id,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "name": "RENAMED",
        "time_zone": "Europe/Moscow",
    }

    assert schedule.name != data["name"]
    assert schedule.time_zone != data["time_zone"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Web schedule update is not enabled through API"}


@pytest.mark.django_db
def test_update_ical_url_overrides_calendar_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        channel=slack_channel_id,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {"ical_url_overrides": ICAL_URL}

    with patch("common.api_helpers.utils.validate_ical_url", return_value=ICAL_URL):
        response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

        result = {
            "id": schedule.public_primary_key,
            "team_id": None,
            "name": schedule.name,
            "type": "calendar",
            "time_zone": schedule.time_zone,
            "on_call_now": [],
            "shifts": [],
            "slack": {
                "channel_id": "SLACKCHANNELID",
                "user_group_id": None,
            },
            "ical_url_overrides": ICAL_URL,
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == result


@pytest.mark.django_db
def test_update_calendar_schedule_with_custom_event(
    make_organization_and_user_with_token,
    make_schedule,
    make_on_call_shift,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        channel=slack_channel_id,
    )
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "shifts": [on_call_shift.public_primary_key],
    }

    assert len(schedule.custom_on_call_shifts.all()) == 0

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "calendar",
        "time_zone": schedule.time_zone,
        "on_call_now": [],
        "shifts": data["shifts"],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
        "ical_url_overrides": None,
    }

    assert response.status_code == status.HTTP_200_OK
    schedule.refresh_from_db()
    assert len(schedule.custom_on_call_shifts.all()) == 1
    assert response.json() == result


@pytest.mark.django_db
def test_update_calendar_schedule_invalid_override(
    make_organization_and_user_with_token,
    make_schedule,
    make_on_call_shift,
):
    organization, _, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
    )
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **data)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "shifts": [on_call_shift.public_primary_key],
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Shifts of type override are not supported in this schedule"}


@pytest.mark.django_db
@pytest.mark.parametrize("ScheduleClass", [OnCallScheduleWeb, OnCallScheduleCalendar])
def test_update_schedule_invalid_timezone(make_organization_and_user_with_token, make_schedule, ScheduleClass):
    organization, _, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(organization, schedule_class=ScheduleClass)
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=10800),
    }

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {"time_zone": "asdfasdf"}

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"time_zone": ["Invalid timezone"]}


@pytest.mark.django_db
def test_update_web_schedule_with_override(
    make_organization_and_user_with_token,
    make_schedule,
    make_on_call_shift,
):
    organization, _, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
    )
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **data)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "shifts": [on_call_shift.public_primary_key],
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Web schedule update is not enabled through API"}


@pytest.mark.django_db
def test_delete_calendar_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(OnCallSchedule.DoesNotExist):
        schedule.refresh_from_db()


@pytest.mark.django_db
def test_get_ical_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        channel=slack_channel_id,
        ical_url_primary=ICAL_URL,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "ical",
        "ical_url_primary": ICAL_URL,
        "ical_url_overrides": None,
        "on_call_now": [],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result


@pytest.mark.django_db
def test_create_ical_schedule(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")
    data = {
        "team_id": None,
        "name": "schedule test name",
        "ical_url_primary": ICAL_URL,
        "type": "ical",
    }

    with patch(
        "apps.public_api.serializers.schedules_ical.ScheduleICalSerializer.validate_ical_url_primary",
        return_value=ICAL_URL,
    ):
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    schedule = OnCallSchedule.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": schedule.name,
        "type": "ical",
        "ical_url_primary": ICAL_URL,
        "ical_url_overrides": None,
        "on_call_now": [],
        "slack": {
            "channel_id": None,
            "user_group_id": None,
        },
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == result


@pytest.mark.django_db
def test_update_ical_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    slack_channel_id = "SLACKCHANNELID"

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        channel=slack_channel_id,
        ical_url_primary=ICAL_URL,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "name": "RENAMED",
    }

    assert schedule.name != data["name"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": schedule.public_primary_key,
        "team_id": None,
        "name": data["name"],
        "type": "ical",
        "ical_url_primary": ICAL_URL,
        "ical_url_overrides": None,
        "on_call_now": [],
        "slack": {
            "channel_id": "SLACKCHANNELID",
            "user_group_id": None,
        },
    }

    assert response.status_code == status.HTTP_200_OK
    schedule.refresh_from_db()
    assert schedule.name == data["name"]
    assert response.json() == result


@pytest.mark.django_db
def test_delete_ical_schedule(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        ical_url_primary=ICAL_URL,
    )

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(OnCallSchedule.DoesNotExist):
        schedule.refresh_from_db()


@pytest.mark.django_db
def test_get_schedule_list(
    make_slack_team_identity,
    make_organization,
    make_user_for_organization,
    make_public_api_token,
    make_slack_user_group,
    make_schedule,
):
    slack_team_identity = make_slack_team_identity()
    organization = make_organization(slack_team_identity=slack_team_identity)
    user = make_user_for_organization(organization=organization)
    _, token = make_public_api_token(user, organization)

    slack_channel_id = "SLACKCHANNELID"
    user_group_id = "SLACKGROUPID"

    user_group = make_slack_user_group(slack_team_identity, slack_id=user_group_id)

    schedule_calendar = make_schedule(
        organization, schedule_class=OnCallScheduleCalendar, channel=slack_channel_id, user_group=user_group
    )

    schedule_ical = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        channel=slack_channel_id,
        ical_url_primary=ICAL_URL,
        user_group=user_group,
    )

    client = APIClient()
    url = reverse("api-public:schedules-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": schedule_calendar.public_primary_key,
                "team_id": None,
                "name": schedule_calendar.name,
                "type": "calendar",
                "time_zone": "UTC",
                "on_call_now": [],
                "shifts": [],
                "slack": {"channel_id": slack_channel_id, "user_group_id": user_group_id},
                "ical_url_overrides": None,
            },
            {
                "id": schedule_ical.public_primary_key,
                "team_id": None,
                "name": schedule_ical.name,
                "type": "ical",
                "ical_url_primary": ICAL_URL,
                "ical_url_overrides": None,
                "on_call_now": [],
                "slack": {"channel_id": slack_channel_id, "user_group_id": user_group_id},
            },
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result


@pytest.mark.django_db
def test_create_schedule_wrong_type(make_organization_and_user_with_token):
    _, _, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")
    data = {
        "team_id": None,
        "name": "schedule test name",
        "ical_url_primary": ICAL_URL,
        "type": "wrong_type",
    }

    with patch(
        "apps.public_api.serializers.schedules_ical.ScheduleICalSerializer.validate_ical_url_primary",
        return_value=ICAL_URL,
    ):
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize("schedule_type", ["web", "calendar"])
def test_create_schedule_invalid_timezone(make_organization_and_user_with_token, schedule_type):
    _, _, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")

    data = {
        "team_id": None,
        "name": "schedule test name",
        "time_zone": "asdfasdasdf",
        "type": schedule_type,
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"time_zone": ["Invalid timezone"]}


@pytest.mark.django_db
def test_create_ical_schedule_without_ical_url(make_organization_and_user_with_token):
    _, _, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:schedules-list")
    data = {
        "team_id": None,
        "name": "schedule test name",
        "type": "ical",
    }
    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = {
        "team_id": None,
        "name": "schedule test name",
        "ical_url_primary": None,
        "type": "ical",
    }
    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_oncall_shifts_request_validation(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, _, token = make_organization_and_user_with_token()
    web_schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    valid_date_msg = "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."

    client = APIClient()

    def _make_request(schedule, query_params=""):
        url = reverse("api-public:schedules-final-shifts", kwargs={"pk": schedule.public_primary_key})
        return client.get(f"{url}{query_params}", format="json", HTTP_AUTHORIZATION=token)

    # query param validation
    response = _make_request(web_schedule, "?start_date=2021-01-01")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["end_date"][0] == "This field is required."

    response = _make_request(web_schedule, "?start_date=asdfasdf")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["start_date"][0] == valid_date_msg

    response = _make_request(web_schedule, "?end_date=2021-01-01")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["start_date"][0] == "This field is required."

    response = _make_request(web_schedule, "?start_date=2021-01-01&end_date=asdfasdf")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["end_date"][0] == valid_date_msg

    response = _make_request(web_schedule, "?end_date=2021-01-01&start_date=2022-01-01")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "non_field_errors": [
            "start_date must be less than or equal to end_date",
        ]
    }

    response = _make_request(web_schedule, "?end_date=2021-01-01&start_date=2019-12-31")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "non_field_errors": [
            "The difference between start_date and end_date must be less than one year (365 days)",
        ]
    }


@pytest.mark.django_db
def test_oncall_shifts_export(
    make_organization_and_user_with_token,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, token = make_organization_and_user_with_token()

    user1_email = "alice909450945045@example.com"
    user2_email = "bob123123123123123@example.com"
    user1_username = "alice"
    user2_username = "bob"

    user1 = make_user(organization=organization, email=user1_email, username=user1_username)
    user2 = make_user(organization=organization, email=user2_email, username=user2_username)

    user1_public_primary_key = user1.public_primary_key
    user2_public_primary_key = user2.public_primary_key
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    start_date = timezone.datetime(2023, 1, 1, 9, 0, 0, tzinfo=pytz.UTC)
    make_on_call_shift(
        organization=organization,
        schedule=schedule,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        priority_level=1,
        interval=1,
        by_day=["MO", "WE", "FR"],
        start=start_date,
        until=start_date + timezone.timedelta(days=28),
        rolling_users=[{user1.pk: user1_public_primary_key}, {user2.pk: user2_public_primary_key}],
        rotation_start=start_date,
        duration=timezone.timedelta(hours=8),
    )

    client = APIClient()

    url = reverse("api-public:schedules-final-shifts", kwargs={"pk": schedule.public_primary_key})
    response = client.get(f"{url}?start_date=2023-01-01&end_date=2023-02-01", format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK

    expected_on_call_times = {
        # 3 shifts per week x 4 weeks x 8 hours per shift = 96 / 2 users = 48h per user for this period
        user1.public_primary_key: 48,
        user2.public_primary_key: 48,
    }
    assert_expected_shifts_export_response(response, (user1, user2), expected_on_call_times)


@pytest.mark.django_db
def test_oncall_shifts_export_from_ical_schedule(
    make_organization_and_user_with_token,
    make_user,
    make_schedule,
):
    organization, _, token = make_organization_and_user_with_token()
    user1 = make_user(organization=organization)
    user2 = make_user(organization=organization)

    ical_data = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        BEGIN:VEVENT
        DTSTART:20230601T090000Z
        DTEND:20230601T180000Z
        RRULE:FREQ=DAILY
        DTSTAMP:20230601T090000Z
        UID:something@google.com
        CREATED:20230601T090000Z
        DESCRIPTION:
        STATUS:CONFIRMED
        SUMMARY:{}
        END:VEVENT
        BEGIN:VEVENT
        DTSTART:20230601T180000Z
        DTEND:20230601T210000Z
        RRULE:FREQ=DAILY
        DTSTAMP:20230601T090000Z
        UID:somethingelse@google.com
        CREATED:20230601T090000Z
        DESCRIPTION:
        STATUS:CONFIRMED
        SUMMARY:{}
        END:VEVENT
        END:VCALENDAR
    """.format(
            user1.username, user2.username
        )
    )
    schedule = make_schedule(organization, schedule_class=OnCallScheduleICal, cached_ical_file_primary=ical_data)

    client = APIClient()

    url = reverse("api-public:schedules-final-shifts", kwargs={"pk": schedule.public_primary_key})
    response = client.get(f"{url}?start_date=2023-07-01&end_date=2023-08-01", format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK

    expected_on_call_times = {
        user1.public_primary_key: 279,  # daily 9h * 31d
        user2.public_primary_key: 93,  # daily 3h * 31d
    }
    assert_expected_shifts_export_response(response, (user1, user2), expected_on_call_times)


@pytest.mark.django_db
def test_oncall_shifts_export_from_api_schedule(
    make_organization_and_user_with_token,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, token = make_organization_and_user_with_token()
    user1 = make_user(organization=organization)
    user2 = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    start_date = timezone.datetime(2023, 1, 1, 9, 0, 0, tzinfo=pytz.UTC)
    on_call_shift = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        start=start_date,
        rotation_start=start_date,
        duration=timezone.timedelta(hours=2),
        start_rotation_from_user_index=1,
    )
    on_call_shift.add_rolling_users([[user1], [user2]])
    schedule.custom_on_call_shifts.add(on_call_shift)

    client = APIClient()

    url = reverse("api-public:schedules-final-shifts", kwargs={"pk": schedule.public_primary_key})
    response = client.get(f"{url}?start_date=2023-07-01&end_date=2023-08-01", format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK

    expected_on_call_times = {
        user1.public_primary_key: 32,  # daily 2h * 16d
        user2.public_primary_key: 30,  # daily 2h * 15d
    }
    assert_expected_shifts_export_response(response, (user1, user2), expected_on_call_times)
