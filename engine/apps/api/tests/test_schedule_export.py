import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.auth_token.models import ScheduleExportAuthToken
from apps.schedules.models import OnCallScheduleICal
from common.constants.role import Role

ICAL_URL = "https://calendar.google.com/calendar/ical/amixr.io_37gttuakhrtr75ano72p69rt78%40group.calendar.google.com/private-1d00a680ba5be7426c3eb3ef1616e26d/basic.ics"  # noqa


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_get_schedule_export_token(
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

    ScheduleExportAuthToken.create_auth_token(user=user, organization=organization, schedule=schedule)

    client = APIClient()

    url = reverse("api-internal:schedule-export-token", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_404_NOT_FOUND),
        (Role.EDITOR, status.HTTP_404_NOT_FOUND),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_export_token_not_found(
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

    url = reverse("api-internal:schedule-export-token", kwargs={"pk": schedule.public_primary_key})

    client = APIClient()

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_201_CREATED),
        (Role.EDITOR, status.HTTP_201_CREATED),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_create_export_token(
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

    url = reverse("api-internal:schedule-export-token", kwargs={"pk": schedule.public_primary_key})

    client = APIClient()

    response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert expected_status == response.status_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_204_NO_CONTENT),
        (Role.EDITOR, status.HTTP_204_NO_CONTENT),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_schedule_delete_export_token(
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

    instance, _ = ScheduleExportAuthToken.create_auth_token(user=user, organization=organization, schedule=schedule)

    url = reverse("api-internal:schedule-export-token", kwargs={"pk": schedule.public_primary_key})

    client = APIClient()

    response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert expected_status == response.status_code

    if response.status_code != 403:
        check_token = ScheduleExportAuthToken.objects.filter(id=instance.id)

        assert len(check_token) == 0
