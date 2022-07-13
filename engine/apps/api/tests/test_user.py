from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.base.constants import ADMIN_PERMISSIONS, EDITOR_PERMISSIONS
from apps.base.models import UserNotificationPolicy
from apps.user_management.models.user import default_working_hours
from common.constants.role import Role


@pytest.mark.django_db
def test_update_user(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)

    team = make_team(organization)
    team.users.add(admin)

    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    data = {
        "unverified_phone_number": "+79123456789",
        "current_team": team.public_primary_key,
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["unverified_phone_number"] == data["unverified_phone_number"]
    assert response.json()["current_team"] == data["current_team"]


@pytest.mark.django_db
def test_update_user_cant_change_email_and_username(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    phone_number = "+79123456789"
    data = {
        "unverified_phone_number": phone_number,
        "email": "test@amixr.io",
        "username": "bob",
    }
    expected_response = {
        "pk": admin.public_primary_key,
        "organization": {"pk": organization.public_primary_key, "name": organization.org_title},
        "current_team": None,
        "email": admin.email,
        "username": admin.username,
        "role": admin.role,
        "timezone": None,
        "working_hours": default_working_hours(),
        "unverified_phone_number": phone_number,
        "verified_phone_number": None,
        "telegram_configuration": None,
        "messaging_backends": {
            "TESTONLY": {
                "user": admin.username,
            }
        },
        "cloud_connection_status": 0,
        "permissions": ADMIN_PERMISSIONS,
        "notification_chain_verbal": {"default": "", "important": ""},
        "slack_user_identity": None,
        "avatar": admin.avatar_url,
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_list_users(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-list")

    expected_payload = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "pk": admin.public_primary_key,
                "organization": {"pk": organization.public_primary_key, "name": organization.org_title},
                "current_team": None,
                "email": admin.email,
                "username": admin.username,
                "role": admin.role,
                "timezone": None,
                "working_hours": default_working_hours(),
                "unverified_phone_number": None,
                "verified_phone_number": None,
                "telegram_configuration": None,
                "messaging_backends": {
                    "TESTONLY": {
                        "user": admin.username,
                    }
                },
                "permissions": ADMIN_PERMISSIONS,
                "notification_chain_verbal": {"default": "", "important": ""},
                "slack_user_identity": None,
                "avatar": admin.avatar_url,
                "cloud_connection_status": 0,
            },
            {
                "pk": editor.public_primary_key,
                "organization": {"pk": organization.public_primary_key, "name": organization.org_title},
                "current_team": None,
                "email": editor.email,
                "username": editor.username,
                "role": editor.role,
                "timezone": None,
                "working_hours": default_working_hours(),
                "unverified_phone_number": None,
                "verified_phone_number": None,
                "telegram_configuration": None,
                "messaging_backends": {
                    "TESTONLY": {
                        "user": editor.username,
                    }
                },
                "permissions": EDITOR_PERMISSIONS,
                "notification_chain_verbal": {"default": "", "important": ""},
                "slack_user_identity": None,
                "avatar": editor.avatar_url,
                "cloud_connection_status": 0,
            },
        ],
    }

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_notification_chain_verbal(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    make_user_notification_policy,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    data_for_creation = [
        {"step": UserNotificationPolicy.Step.NOTIFY, "notify_by": UserNotificationPolicy.NotificationChannel.SLACK},
        {"step": UserNotificationPolicy.Step.WAIT, "wait_delay": timezone.timedelta(minutes=5)},
        {
            "step": UserNotificationPolicy.Step.NOTIFY,
            "notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        },
        {"step": UserNotificationPolicy.Step.WAIT, "wait_delay": None},
        {"step": UserNotificationPolicy.Step.NOTIFY, "notify_by": UserNotificationPolicy.NotificationChannel.TELEGRAM},
        {"step": None},
        {
            "step": UserNotificationPolicy.Step.NOTIFY,
            "notify_by": UserNotificationPolicy.NotificationChannel.SLACK,
            "important": True,
        },
        {"step": UserNotificationPolicy.Step.WAIT, "wait_delay": timezone.timedelta(minutes=5), "important": True},
        {
            "step": UserNotificationPolicy.Step.NOTIFY,
            "notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL,
            "important": True,
        },
        {"step": UserNotificationPolicy.Step.WAIT, "wait_delay": None, "important": True},
        {
            "step": UserNotificationPolicy.Step.NOTIFY,
            "notify_by": UserNotificationPolicy.NotificationChannel.TELEGRAM,
            "important": True,
        },
    ]

    for data in data_for_creation:
        make_user_notification_policy(admin, **data)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})

    expected_notification_chain = {
        "default": "Slack - 5 min - \U0000260E - Telegram",
        "important": "Slack - 5 min - \U0000260E - Telegram",
    }

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["notification_chain_verbal"] == expected_notification_chain


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_update_self_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)
    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": tester.public_primary_key})
    with patch(
        "apps.api.views.user.UserView.update",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(tester, token))

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
def test_user_update_other_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    data = {"unverified_phone_number": "+79123456789"}

    response = client.put(url, data, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_list_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-list")
    with patch(
        "apps.api.views.user.UserView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_user_detail_self_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": tester.public_primary_key})
    with patch(
        "apps.api.views.user.UserView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_user_detail_other_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_get_own_verification_code(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": tester.public_primary_key})
    with patch(
        "apps.api.views.user.UserView.get_verification_code",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_user_get_other_verification_code(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": admin.public_primary_key})
    with patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock()):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_verify_own_phone(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": tester.public_primary_key})
    with patch(
        "apps.api.views.user.UserView.verify_number",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


"""
Tests below are outdated
"""


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_verify_another_phone(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    other_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": other_user.public_primary_key})

    with patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None)):
        response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_get_own_telegram_verification_code(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": tester.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(tester, token))
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
def test_user_get_another_telegram_verification_code(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=role)
    other_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": other_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(tester, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_admin_can_update_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    tester = make_user_for_organization(organization, role=Role.ADMIN)
    other_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "role": Role.ADMIN,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }
    url = reverse("api-internal:user-detail", kwargs={"pk": other_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_update_himself(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "role": Role.ADMIN,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_list_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    url = reverse("api-internal:user-list")
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_detail_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    url = reverse("api-internal:user-detail", kwargs={"pk": editor.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_admin_can_get_own_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": admin.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_admin_can_get_another_user_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": editor.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_admin_can_verify_own_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": admin.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_admin_can_verify_another_user_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": editor.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_own_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": admin.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_another_user_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": editor.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_another_user_backend_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": editor.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_unlink_another_user_backend_account(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": editor.public_primary_key}) + "?backend=TESTONLY"

    response = client.post(url, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


"""Test user permissions"""


@pytest.mark.django_db
def test_user_cant_update_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "role": Role.ADMIN,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_update_themself(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "role": Role.EDITOR,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_can_list_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    url = reverse("api-internal:user-list")
    response = client.get(url, format="json", **make_user_auth_headers(editor, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_can_detail_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    editor = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(editor, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_user_can_get_own_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_user_cant_get_another_user_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_user_can_verify_own_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_user_cant_verify_another_user_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": first_user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_get_own_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_cant_get_another_user_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_get_own_backend_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": user.public_primary_key})
        + "?backend=TESTONLY"
    )

    with patch(
        "apps.base.tests.messaging_backend.TestOnlyBackend.generate_user_verification_code",
        return_value="the-code",
    ) as mock_generate_code:
        response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "the-code"
    mock_generate_code.assert_called_once_with(user)


@pytest.mark.django_db
def test_user_cant_get_another_user_backend_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": first_user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_unlink_backend_own_account(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=TESTONLY"

    response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_unlink_backend_invalid_backend_id(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=INVALID"

    response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_unlink_backend_backend_account_not_found(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=TESTONLY"
    with patch("apps.base.tests.messaging_backend.TestOnlyBackend.unlink_user", side_effect=ObjectDoesNotExist):
        response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_cant_unlink_backend__another_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-unlink-backend", kwargs={"pk": first_user.public_primary_key}) + "?backend=TESTONLY"
    )

    response = client.post(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


"""Test stakeholder permissions"""


@pytest.mark.django_db
def test_viewer_cant_create_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-list")
    data = {
        "email": "test@amixr.io",
        "role": Role.ADMIN,
        "username": "test_username",
        "unverified_phone_number": None,
        "slack_login": "",
    }
    response = client.post(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_update_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    data = {
        "email": "test@amixr.io",
        "role": Role.EDITOR,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_update_himself(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    data = {
        "email": "test@amixr.io",
        "role": Role.VIEWER,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_list_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-list")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_detail_users(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_viewer_cant_get_own_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.send_verification_code", return_value=Mock())
@pytest.mark.django_db
def test_viewer_cant_get_another_user_verification_code(
    mock_verification_start,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_viewer_cant_verify_own_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.twilioapp.phone_manager.PhoneManager.verify_phone_number", return_value=(True, None))
@pytest.mark.django_db
def test_viewer_cant_verify_another_user_phone(
    mocked_verification_check,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": first_user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_get_own_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_get_another_user_telegram_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status,initial_unverified_number,initial_verified_number",
    [
        (Role.ADMIN, status.HTTP_200_OK, "+1234567890", None),
        (Role.EDITOR, status.HTTP_200_OK, "+1234567890", None),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (Role.ADMIN, status.HTTP_200_OK, None, "+1234567890"),
        (Role.EDITOR, status.HTTP_200_OK, None, "+1234567890"),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
    ],
)
def test_forget_own_number(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
    initial_unverified_number,
    initial_verified_number,
):
    organization = make_organization()
    admin = make_user_for_organization(organization, role=Role.ADMIN)
    user = make_user_for_organization(
        organization,
        role=role,
        unverified_phone_number=initial_unverified_number,
        _verified_phone_number=initial_verified_number,
    )
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-forget-number", kwargs={"pk": user.public_primary_key})
    with patch(
        "apps.twilioapp.phone_manager.PhoneManager.notify_about_changed_verified_phone_number", return_value=None
    ):
        response = client.put(url, None, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == expected_status

    user_detail_url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.get(user_detail_url, None, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK
    if expected_status == status.HTTP_200_OK:
        assert not response.json()["unverified_phone_number"]
        assert not response.json()["verified_phone_number"]
    else:
        assert response.json()["unverified_phone_number"] == initial_unverified_number
        assert response.json()["verified_phone_number"] == initial_verified_number


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status,initial_unverified_number,initial_verified_number",
    [
        (Role.ADMIN, status.HTTP_200_OK, "+1234567890", None),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (Role.ADMIN, status.HTTP_200_OK, None, "+1234567890"),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
    ],
)
def test_forget_other_number(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
    initial_unverified_number,
    initial_verified_number,
):
    organization = make_organization()
    user = make_user_for_organization(
        organization,
        role=Role.ADMIN,
        unverified_phone_number=initial_unverified_number,
        _verified_phone_number=initial_verified_number,
    )
    other_user = make_user_for_organization(organization, role=role)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-forget-number", kwargs={"pk": user.public_primary_key})
    with patch(
        "apps.twilioapp.phone_manager.PhoneManager.notify_about_changed_verified_phone_number", return_value=None
    ):
        response = client.put(url, None, format="json", **make_user_auth_headers(other_user, token))
        assert response.status_code == expected_status

    user_detail_url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.get(user_detail_url, None, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    if expected_status == status.HTTP_200_OK:
        assert not response.json()["unverified_phone_number"]
        assert not response.json()["verified_phone_number"]
    else:
        assert response.json()["unverified_phone_number"] == initial_unverified_number
        assert response.json()["verified_phone_number"] == initial_verified_number


@pytest.mark.django_db
def test_viewer_cant_get_own_backend_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_get_another_user_backend_verification_code(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": first_user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_unlink_backend_own_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=TESTONLY"

    response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_unlink_backend_another_user(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    first_user = make_user_for_organization(organization, role=Role.EDITOR)
    second_user = make_user_for_organization(organization, role=Role.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = (
        reverse("api-internal:user-unlink-backend", kwargs={"pk": first_user.public_primary_key}) + "?backend=TESTONLY"
    )

    response = client.post(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_change_timezone(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    data = {"timezone": "Europe/London"}

    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert "timezone" in response.json()
    assert response.json()["timezone"] == "Europe/London"


@pytest.mark.django_db
@pytest.mark.parametrize("timezone", ["", 1, "NotATimezone"])
def test_invalid_timezone(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers, timezone
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    data = {"timezone": timezone}

    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_working_hours(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    periods = [{"start": "05:00:00", "end": "23:00:00"}]
    working_hours = {
        day: periods for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    }

    data = {"working_hours": working_hours}

    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert "working_hours" in response.json()
    assert response.json()["working_hours"] == working_hours


@pytest.mark.django_db
@pytest.mark.parametrize(
    "working_hours_extra",
    [
        {},
        {"sunday": 1},
        {"sunday": ""},
        {"sunday": {"start": "18:00:00"}},
        {"sunday": {"start": "", "end": ""}},
        {"sunday": {"start": "18:00:00", "end": None}},
        {"sunday": {"start": "18:00:00", "end": "18:00:00"}},
        {"sunday": {"start": "18:00:00", "end": "9:00:00"}},
        {"sunday": {"start": "18:00:00", "end": "9:00:00", "extra": 1}},
    ],
)
def test_invalid_working_hours(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    working_hours_extra,
):
    organization = make_organization()
    user = make_user_for_organization(organization, role=Role.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    periods = [{"start": "05:00:00", "end": "23:00:00"}]
    working_hours = {day: periods for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]}
    working_hours.update(working_hours_extra)

    data = {"working_hours": working_hours}
    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
