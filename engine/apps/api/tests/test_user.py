from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import GrafanaAPIPermission, LegacyAccessControlRole, RBACPermission
from apps.base.models import UserNotificationPolicy
from apps.phone_notifications.exceptions import FailedToFinishVerification
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.user_management.models.user import default_working_hours


@pytest.fixture(autouse=True)
def clear_cache():
    # Ratelimit keys are stored in cache, clean to prevent ratelimits
    cache.clear()


@pytest.mark.django_db
def test_current_user(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:api-user")

    expected_response = {
        "pk": user.public_primary_key,
        "organization": {"pk": organization.public_primary_key, "name": organization.org_title},
        "current_team": None,
        "email": user.email,
        "hide_phone_number": False,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "rbac_permissions": user.permissions,
        "timezone": None,
        "working_hours": default_working_hours(),
        "unverified_phone_number": None,
        "verified_phone_number": None,
        "telegram_configuration": None,
        "messaging_backends": {
            "TESTONLY": {
                "user": user.username,
            }
        },
        "cloud_connection_status": 0,
        "notification_chain_verbal": {"default": "", "important": ""},
        "slack_user_identity": None,
        "avatar": user.avatar_url,
        "avatar_full": user.avatar_full_url,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    data_to_update = {"hide_phone_number": True}

    response = client.put(url, data=data_to_update, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response | data_to_update


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


@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
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
        "hide_phone_number": False,
        "username": admin.username,
        "name": admin.name,
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
        "cloud_connection_status": None,
        "notification_chain_verbal": {"default": "", "important": ""},
        "slack_user_identity": None,
        "avatar": admin.avatar_url,
        "avatar_full": admin.avatar_full_url,
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
@pytest.mark.django_db
def test_list_users(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    editor = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
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
                "hide_phone_number": False,
                "username": admin.username,
                "name": admin.name,
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
                "notification_chain_verbal": {"default": "", "important": ""},
                "slack_user_identity": None,
                "avatar": admin.avatar_url,
                "avatar_full": admin.avatar_full_url,
                "cloud_connection_status": None,
            },
            {
                "pk": editor.public_primary_key,
                "organization": {"pk": organization.public_primary_key, "name": organization.org_title},
                "current_team": None,
                "email": editor.email,
                "hide_phone_number": False,
                "username": editor.username,
                "name": editor.name,
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
                "notification_chain_verbal": {"default": "", "important": ""},
                "slack_user_identity": None,
                "avatar": editor.avatar_url,
                "avatar_full": editor.avatar_full_url,
                "cloud_connection_status": None,
            },
        ],
        "current_page_number": 1,
        "page_size": 100,
        "total_pages": 1,
    }

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_list_users_filtered_by_granted_permission(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    perm_to_filter_on = RBACPermission.Permissions.NOTIFICATIONS_READ.value
    perms_to_grant = [GrafanaAPIPermission(action=perm_to_filter_on)]

    organization = make_organization()
    admin_user = make_user_for_organization(organization)
    user1 = make_user_for_organization(organization, permissions=perms_to_grant)
    user2 = make_user_for_organization(organization, permissions=perms_to_grant)
    user3 = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-list")

    response = client.get(
        f"{url}?permission={perm_to_filter_on}", format="json", **make_user_auth_headers(admin_user, token)
    )

    assert response.status_code == status.HTTP_200_OK
    returned_user_pks = [u["pk"] for u in response.json()["results"]]

    assert admin_user.public_primary_key in returned_user_pks
    assert user1.public_primary_key in returned_user_pks
    assert user2.public_primary_key in returned_user_pks
    assert user3.public_primary_key not in returned_user_pks


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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_update_self_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_update_other_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)
    admin = make_user_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    data = {"unverified_phone_number": "+79123456789"}

    response = client.put(url, data, format="json", **make_user_auth_headers(tester, token))

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
def test_user_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)

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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_user_detail_self_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)

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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_detail_other_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)
    admin = make_user_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": admin.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_user_get_own_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)

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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_get_other_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)
    admin = make_user_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": admin.public_primary_key})
    with patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock()):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_validation_of_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})
    with patch(
        "apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True
    ) as verify_phone_number:
        url_with_token = f"{url}?token=some_token"
        r = client.put(url_with_token, format="json", **make_user_auth_headers(user, token))
        assert r.status_code == 200
        assert verify_phone_number.call_count == 1

        url_without_token = f"{url}"
        r = client.put(url_without_token, format="json", **make_user_auth_headers(user, token))
        assert r.status_code == 400
        assert verify_phone_number.call_count == 1

        url_with_empty_token = f"{url}?token="
        r = client.put(url_with_empty_token, format="json", **make_user_auth_headers(user, token))
        assert r.status_code == 400
        assert verify_phone_number.call_count == 1


@pytest.mark.django_db
def test_verification_code_provider_exception(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})
    with patch(
        "apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number",
        side_effect=FailedToFinishVerification,
    ) as verify_phone_number:
        url_with_token = f"{url}?token=some_token"
        r = client.put(url_with_token, format="json", **make_user_auth_headers(user, token))
        assert r.status_code == 503
        assert verify_phone_number.call_count == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_verify_own_phone(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)

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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_verify_another_phone(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)
    other_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": other_user.public_primary_key})

    with patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True):
        response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(tester, token))

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
def test_user_get_own_telegram_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": tester.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(tester, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_user_get_another_telegram_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)
    other_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": other_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(tester, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_admin_can_update_user(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_update_himself(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_list_users(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.ADMIN)

    client = APIClient()

    url = reverse("api-internal:user-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_detail_users(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()

    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_admin_can_get_own_verification_code(
    mock_verification_start,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_admin_can_get_another_user_verification_code(
    mock_verification_start,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": first_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_admin_can_verify_own_phone(
    mocked_verification_check,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.ADMIN)
    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_admin_can_verify_another_user_phone(
    mocked_verification_check,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": first_user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_own_telegram_verification_code(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_another_user_telegram_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_get_another_user_backend_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": first_user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_unlink_another_user_backend_account(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = (
        reverse("api-internal:user-unlink-backend", kwargs={"pk": first_user.public_primary_key}) + "?backend=TESTONLY"
    )

    response = client.post(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_unlink_another_user_slack_account(
    make_organization_with_slack_team_identity,
    make_user_for_organization,
    make_user_with_slack_user_identity,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    _, token = make_token_for_organization(organization)

    user, _ = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_2", role=LegacyAccessControlRole.ADMIN
    )
    other_user = make_user_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-unlink-slack", kwargs={"pk": other_user.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    other_user.refresh_from_db()
    assert other_user.slack_user_identity is None


"""Test user permissions"""


@pytest.mark.django_db
def test_user_cant_update_user(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_update_themself(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    data = {
        "email": "test@amixr.io",
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_can_list_users(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()

    url = reverse("api-internal:user-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_can_detail_users(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_user_can_get_own_verification_code(
    mock_verification_start, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_user_cant_get_another_user_verification_code(
    mock_verification_start,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_user_can_verify_own_phone(
    mocked_verification_check, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_user_cant_verify_another_user_phone(
    mocked_verification_check,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": first_user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_get_own_telegram_verification_code(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_cant_get_another_user_telegram_verification_code(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_get_own_backend_verification_code(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

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
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": first_user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_unlink_own_slack_account(
    make_organization_with_slack_team_identity,
    make_user_with_slack_user_identity,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user, _ = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_2", role=LegacyAccessControlRole.EDITOR
    )

    _, token = make_token_for_organization(organization)
    client = APIClient()
    url = reverse("api-internal:user-unlink-slack", kwargs={"pk": user.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.slack_user_identity is None


@pytest.mark.django_db
def test_user_can_unlink_backend_own_account(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=TESTONLY"

    response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_unlink_backend_invalid_backend_id(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=INVALID"

    response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_unlink_backend_backend_account_not_found(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-unlink-backend", kwargs={"pk": user.public_primary_key}) + "?backend=TESTONLY"
    with patch("apps.base.tests.messaging_backend.TestOnlyBackend.unlink_user", side_effect=ObjectDoesNotExist):
        response = client.post(f"{url}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_cant_unlink_slack_another_user(
    make_organization_with_slack_team_identity,
    make_user_with_slack_user_identity,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    first_user, _ = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_1", role=LegacyAccessControlRole.EDITOR
    )
    second_user, _ = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_2", role=LegacyAccessControlRole.EDITOR
    )

    _, token = make_token_for_organization(organization)
    client = APIClient()
    url = reverse("api-internal:user-unlink-slack", kwargs={"pk": first_user.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    first_user.refresh_from_db()
    assert first_user.slack_user_identity is not None


@pytest.mark.django_db
def test_user_cant_unlink_backend_another_user(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = (
        reverse("api-internal:user-unlink-backend", kwargs={"pk": first_user.public_primary_key}) + "?backend=TESTONLY"
    )

    response = client.post(f"{url}", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


"""Test stakeholder permissions"""


@pytest.mark.django_db
def test_viewer_cant_update_user(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    data = {
        "email": "test@amixr.io",
        "role": LegacyAccessControlRole.EDITOR,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_update_himself(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    data = {
        "email": "test@amixr.io",
        "role": LegacyAccessControlRole.VIEWER,
        "username": "updated_test_username",
        "unverified_phone_number": "+1234567890",
        "slack_login": "",
    }

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})
    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_list_users(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-list")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_detail_users(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": first_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_viewer_cant_get_own_verification_code(
    mock_verification_start, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.django_db
def test_viewer_cant_get_another_user_verification_code(
    mock_verification_start,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_viewer_cant_verify_own_phone(
    mocked_verification_check, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@pytest.mark.django_db
def test_viewer_cant_verify_another_user_phone(
    mocked_verification_check,
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-verify-number", kwargs={"pk": first_user.public_primary_key})

    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_get_own_telegram_verification_code(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": user.public_primary_key})

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_get_another_user_telegram_verification_code(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = reverse("api-internal:user-get-telegram-verification-code", kwargs={"pk": first_user.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status,initial_unverified_number,initial_verified_number",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK, "+1234567890", None),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK, "+1234567890", None),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK, None, "+1234567890"),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK, None, "+1234567890"),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
    ],
)
def test_forget_own_number(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
    initial_unverified_number,
    initial_verified_number,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    user = make_user_for_organization(
        organization,
        role=role,
        unverified_phone_number=initial_unverified_number,
        _verified_phone_number=initial_verified_number,
    )

    client = APIClient()
    url = reverse("api-internal:user-forget-number", kwargs={"pk": user.public_primary_key})
    with patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_disconnected_number", return_value=None):
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK, "+1234567890", None),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN, "+1234567890", None),
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK, None, "+1234567890"),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN, None, "+1234567890"),
    ],
)
def test_forget_other_number(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
    initial_unverified_number,
    initial_verified_number,
):
    organization = make_organization()
    _, token = make_token_for_organization(organization)

    admin = make_user_for_organization(
        organization, unverified_phone_number=initial_unverified_number, _verified_phone_number=initial_verified_number
    )
    other_user = make_user_for_organization(organization, role=role)
    admin_primary_key = admin.public_primary_key

    client = APIClient()
    url = reverse("api-internal:user-forget-number", kwargs={"pk": admin_primary_key})
    with patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_disconnected_number", return_value=None):
        response = client.put(url, None, format="json", **make_user_auth_headers(other_user, token))
        assert response.status_code == expected_status

    user_detail_url = reverse("api-internal:user-detail", kwargs={"pk": admin_primary_key})
    response = client.get(user_detail_url, None, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK

    if expected_status == status.HTTP_200_OK:
        assert not response.json()["unverified_phone_number"]
        assert not response.json()["verified_phone_number"]
    else:
        assert response.json()["unverified_phone_number"] == initial_unverified_number
        assert response.json()["verified_phone_number"] == initial_verified_number


@pytest.mark.django_db
def test_viewer_cant_get_another_user_backend_verification_code(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = (
        reverse("api-internal:user-get-backend-verification-code", kwargs={"pk": first_user.public_primary_key})
        + "?backend=TESTONLY"
    )

    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_viewer_cant_unlink_backend_another_user(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_auth_headers
):
    organization, first_user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    second_user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()
    url = (
        reverse("api-internal:user-unlink-backend", kwargs={"pk": first_user.public_primary_key}) + "?backend=TESTONLY"
    )

    response = client.post(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_change_timezone(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    data = {"timezone": "Europe/London"}

    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert "timezone" in response.json()
    assert response.json()["timezone"] == "Europe/London"


@pytest.mark.django_db
@pytest.mark.parametrize("timezone", ["", 1, "NotATimezone"])
def test_invalid_timezone(make_organization_and_user_with_plugin_token, make_user_auth_headers, timezone):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    data = {"timezone": timezone}

    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_working_hours(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

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
    make_organization_and_user_with_plugin_token, make_user_auth_headers, working_hours_extra
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-detail", kwargs={"pk": user.public_primary_key})

    periods = [{"start": "05:00:00", "end": "23:00:00"}]
    working_hours = {day: periods for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]}
    working_hours.update(working_hours_extra)

    data = {"working_hours": working_hours}
    response = client.put(f"{url}", data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_check_availability(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:user-check-availability", kwargs={"pk": user.public_primary_key})

    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_check_availability_other_user(make_organization_and_user_with_plugin_token, make_user, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    user_to_check = make_user(organization=user.organization, role=LegacyAccessControlRole.ADMIN)

    client = APIClient()
    url = reverse("api-internal:user-check-availability", kwargs={"pk": user_to_check.public_primary_key})

    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@patch(
    "apps.api.throttlers.GetPhoneVerificationCodeThrottlerPerUser.get_throttle_limits",
    return_value=(1, 10 * 60),
)
@patch("apps.api.throttlers.VerifyPhoneNumberThrottlerPerUser.get_throttle_limits", return_value=(1, 10 * 60))
@pytest.mark.django_db
def test_phone_number_verification_flow_ratelimit_per_user(
    mock_verification_start,
    mocked_verification_check,
    mocked_get_phone_verification_code_get_throttle_limits,
    mocked_get_phone_verify_phone_number_limits,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})

    # first get_verification_code request is succesfull
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    # second get_verification_code request is ratelimited
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    # first verify_number request is succesfull, because it uses different ratelimit scope
    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})

    # second verify_number request is succesfull, because it ratelimited
    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@patch("apps.phone_notifications.phone_backend.PhoneBackend.verify_phone_number", return_value=True)
@patch(
    "apps.api.throttlers.GetPhoneVerificationCodeThrottlerPerOrg.get_throttle_limits",
    return_value=(1, 10 * 60),
)
@patch("apps.api.throttlers.VerifyPhoneNumberThrottlerPerOrg.get_throttle_limits", return_value=(1, 10 * 60))
@pytest.mark.django_db
def test_phone_number_verification_flow_ratelimit_per_org(
    mock_verification_start,
    mocked_verification_check,
    mocked_get_phone_verification_code_get_throttle_limits,
    mocked_get_phone_verify_phone_number_limits,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_for_organization,
):
    """
    This test is checks per-org ratelimits for phone verification flow.
    It makes two get_verification_code and two verify_number requests from different users and expect that second call will be ratelimited.
    """
    org, user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(org)

    client = APIClient()

    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": second_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    url = reverse("api-internal:user-verify-number", kwargs={"pk": user.public_primary_key})
    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    url = reverse("api-internal:user-verify-number", kwargs={"pk": second_user.public_primary_key})
    response = client.put(f"{url}?token=12345", format="json", **make_user_auth_headers(second_user, token))
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@patch("apps.phone_notifications.phone_backend.PhoneBackend.send_verification_sms", return_value=Mock())
@pytest.mark.parametrize(
    "recaptcha_testing_pass,expected_status",
    [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_phone_number_verification_recaptcha(
    mock_verification_start,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    recaptcha_testing_pass,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token()

    recaptcha_token = "asdasdfasdf"
    client = APIClient()
    request_headers = {"HTTP_X-OnCall-Recaptcha": recaptcha_token, **make_user_auth_headers(user, token)}
    url = reverse("api-internal:user-get-verification-code", kwargs={"pk": user.public_primary_key})
    with patch("apps.api.views.user.check_recaptcha_internal_api", return_value=recaptcha_testing_pass):
        response = client.get(url, format="json", **request_headers)
        assert response.status_code == expected_status
        if expected_status == status.HTTP_200_OK:
            mock_verification_start.assert_called_once_with(user)
        else:
            mock_verification_start.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "days",
    ["invalid", 75, -2, 0],
)
def test_upcoming_shifts_invalid_days(
    make_organization, make_user_for_organization, make_token_for_organization, make_user_auth_headers, days
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:user-upcoming-shifts", kwargs={"pk": admin.public_primary_key}) + "?days={}".format(
        days
    )

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_upcoming_shifts_oncall(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
    )
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (admin, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    schedule.refresh_ical_final_schedule()

    client = APIClient()

    url = reverse("api-internal:user-upcoming-shifts", kwargs={"pk": admin.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    returned_data = response.data[0]
    assert returned_data["schedule_id"] == schedule.public_primary_key
    assert returned_data["schedule_name"] == schedule.name
    assert returned_data["is_oncall"]
    assert returned_data["current_shift"]["start"] == on_call_shift.start
    next_shift_start = on_call_shift.start + timezone.timedelta(days=1)
    assert returned_data["next_shift"]["start"] == next_shift_start

    # empty response for other user
    url = reverse("api-internal:user-upcoming-shifts", kwargs={"pk": other_user.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_upcoming_shifts_override(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
    )
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)

    override_data = {
        "start": tomorrow + timezone.timedelta(hours=22),
        "rotation_start": tomorrow + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[admin]])
    schedule.refresh_ical_file()
    schedule.refresh_ical_final_schedule()

    client = APIClient()
    url = reverse("api-internal:user-upcoming-shifts", kwargs={"pk": admin.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    returned_data = response.data[0]
    assert returned_data["schedule_id"] == schedule.public_primary_key
    assert returned_data["schedule_name"] == schedule.name
    assert returned_data["is_oncall"] is False
    assert returned_data["current_shift"] is None
    assert returned_data["next_shift"]["start"] == override.start


@pytest.mark.django_db
def test_upcoming_shifts_multiple_schedules(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    schedules = []
    # create schedules in a reversed order to check the output is sorted later
    for i in range(2, -1, -1):
        schedule = make_schedule(
            organization,
            schedule_class=OnCallScheduleWeb,
        )
        shifts = (
            # user, priority, start time (h), duration (seconds)
            (admin, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
        )
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for user, priority, start_h, duration in shifts:
            data = {
                "start": today + timezone.timedelta(hours=start_h) + timezone.timedelta(days=i),
                "rotation_start": today + timezone.timedelta(hours=start_h) + timezone.timedelta(days=i),
                "duration": timezone.timedelta(seconds=duration),
                "priority_level": priority,
                "frequency": CustomOnCallShift.FREQUENCY_DAILY,
                "schedule": schedule,
            }
            on_call_shift = make_on_call_shift(
                organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
            )
            on_call_shift.add_rolling_users([[user]])
        schedule.refresh_ical_file()
        schedule.refresh_ical_final_schedule()
        schedules.append(schedule)

    client = APIClient()
    url = reverse("api-internal:user-upcoming-shifts", kwargs={"pk": admin.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK
    returned_data = response.data
    for i, schedule in enumerate(reversed(schedules)):
        assert returned_data[i]["schedule_name"] == schedule.name
        expected_start = today + timezone.timedelta(hours=start_h) + timezone.timedelta(days=i)
        if i == 0:
            assert returned_data[i]["is_oncall"]
            assert returned_data[i]["current_shift"]["start"] == expected_start
            assert returned_data[i]["next_shift"]["start"] == expected_start + timezone.timedelta(days=1)
        else:
            assert returned_data[i]["is_oncall"] is False
            assert returned_data[i]["current_shift"] is None
            assert returned_data[i]["next_shift"]["start"] == expected_start
