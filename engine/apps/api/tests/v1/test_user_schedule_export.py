import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.auth_token.models import UserScheduleExportAuthToken

ICAL_URL = "https://calendar.google.com/calendar/ical/amixr.io_37gttuakhrtr75ano72p69rt78%40group.calendar.google.com/private-1d00a680ba5be7426c3eb3ef1616e26d/basic.ics"  # noqa


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_get_user_schedule_export_token(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    UserScheduleExportAuthToken.create_auth_token(
        user=user,
        organization=organization,
    )

    client = APIClient()

    url = reverse("api-internal:user-export-token", kwargs={"pk": user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.EDITOR, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_schedule_export_token_not_found(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)

    url = reverse("api-internal:user-export-token", kwargs={"pk": user.public_primary_key})

    client = APIClient()

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.EDITOR, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_schedule_create_export_token(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)

    url = reverse("api-internal:user-export-token", kwargs={"pk": user.public_primary_key})

    client = APIClient()

    response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert expected_status == response.status_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_409_CONFLICT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_409_CONFLICT),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_schedule_create_multiple_export_tokens_fails(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    UserScheduleExportAuthToken.create_auth_token(
        user=user,
        organization=organization,
    )

    url = reverse("api-internal:user-export-token", kwargs={"pk": user.public_primary_key})

    client = APIClient()

    response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert expected_status == response.status_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_schedule_delete_export_token(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    instance, _ = UserScheduleExportAuthToken.create_auth_token(
        user=user,
        organization=organization,
    )

    url = reverse("api-internal:user-export-token", kwargs={"pk": user.public_primary_key})

    client = APIClient()

    response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert expected_status == response.status_code

    if response.status_code != 403:
        check_token = UserScheduleExportAuthToken.objects.filter(id=instance.id)

        assert len(check_token) == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.EDITOR, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_cannot_get_another_users_schedule_token(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization1, user1, _ = make_organization_and_user_with_plugin_token(role)
    _, user2, token2 = make_organization_and_user_with_plugin_token(role)

    UserScheduleExportAuthToken.create_auth_token(
        user=user1,
        organization=organization1,
    )

    url = reverse("api-internal:user-export-token", kwargs={"pk": user1.public_primary_key})

    client = APIClient()

    response = client.get(url, format="json", **make_user_auth_headers(user2, token2))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.EDITOR, status.HTTP_404_NOT_FOUND),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_cannot_delete_another_users_schedule_token(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization1, user1, _ = make_organization_and_user_with_plugin_token(role)
    _, user2, token2 = make_organization_and_user_with_plugin_token(role)

    UserScheduleExportAuthToken.create_auth_token(
        user=user1,
        organization=organization1,
    )

    url = reverse("api-internal:user-export-token", kwargs={"pk": user1.public_primary_key})

    client = APIClient()

    response = client.delete(url, format="json", **make_user_auth_headers(user2, token2))

    assert response.status_code == expected_status
