import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal


@pytest.mark.django_db
def test_direct_paging_new_alert_group(
    make_organization_and_user_with_plugin_token, make_user, make_schedule, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    users_to_page = [
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.ADMIN).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.EDITOR).public_primary_key,
            "important": True,
        },
    ]

    schedules_to_page = [
        {"id": make_schedule(organization, schedule_class=OnCallScheduleICal).public_primary_key, "important": False},
        {
            "id": make_schedule(organization, schedule_class=OnCallScheduleCalendar).public_primary_key,
            "important": True,
        },
    ]

    title = "Test Alert Group"
    message = "Testing direct paging with new alert group"

    client = APIClient()
    url = reverse("api-internal:direct_paging")

    response = client.post(
        url,
        data={"users": users_to_page, "schedules": schedules_to_page, "title": title, "message": message},
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_direct_paging_existing_alert_group(
    make_organization_and_user_with_plugin_token,
    make_user,
    make_schedule,
    make_alert_receive_channel,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    users_to_page = [
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.ADMIN).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.EDITOR).public_primary_key,
            "important": True,
        },
    ]

    schedules_to_page = [
        {"id": make_schedule(organization, schedule_class=OnCallScheduleICal).public_primary_key, "important": False},
        {
            "id": make_schedule(organization, schedule_class=OnCallScheduleCalendar).public_primary_key,
            "important": True,
        },
    ]

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

    response = client.post(
        url,
        data={"users": users_to_page, "schedules": schedules_to_page, "alert_group_id": alert_group.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
