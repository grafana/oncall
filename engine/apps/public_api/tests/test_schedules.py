from unittest.mock import patch

import pytest
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

    start_date = timezone.datetime.now().replace(microsecond=0)
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
    start_date = timezone.datetime.now().replace(microsecond=0)
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
    start_date = timezone.datetime.now().replace(microsecond=0)
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
    start_date = timezone.datetime.now().replace(microsecond=0)
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

    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
    )
    start_date = timezone.datetime.now().replace(microsecond=0)
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
@pytest.only
def test_oncall_shifts_export_doesnt_work_for_ical_schedules(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, _, token = make_organization_and_user_with_token()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleICal)

    client = APIClient()

    url = reverse("api-public:schedules-oncall_shifts_export", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
