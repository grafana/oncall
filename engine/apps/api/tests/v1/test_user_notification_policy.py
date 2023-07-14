import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.base.models import UserNotificationPolicy
from apps.base.tests.messaging_backend import TestOnlyBackend

DEFAULT_NOTIFICATION_CHANNEL = UserNotificationPolicy.NotificationChannel.SLACK


@pytest.fixture()
def user_notification_policy_internal_api_setup(
    make_organization_and_user_with_plugin_token, make_user_for_organization, make_user_notification_policy
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    wait_notification_step = make_user_notification_policy(
        admin, UserNotificationPolicy.Step.WAIT, wait_delay=timezone.timedelta(minutes=15), important=False
    )
    notify_notification_step = make_user_notification_policy(
        admin,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
        important=False,
    )

    important_notification_step = make_user_notification_policy(
        admin,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
        important=True,
    )

    second_user_step = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
        important=False,
    )
    steps = wait_notification_step, notify_notification_step, important_notification_step, second_user_step
    users = admin, user
    return token, steps, users


@pytest.mark.django_db
def test_create_notification_policy(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, _, users = user_notification_policy_internal_api_setup
    admin, _ = users
    client = APIClient()
    url = reverse("api-internal:notification_policy-list")

    data = {
        "step": UserNotificationPolicy.Step.NOTIFY,
        "notify_by": UserNotificationPolicy.NotificationChannel.SLACK,
        "wait_delay": None,
        "important": False,
        "user": admin.public_primary_key,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_admin_can_create_notification_policy_for_user(
    user_notification_policy_internal_api_setup, make_user_auth_headers
):
    token, _, users = user_notification_policy_internal_api_setup
    admin, user = users
    client = APIClient()
    url = reverse("api-internal:notification_policy-list")

    data = {
        "step": UserNotificationPolicy.Step.NOTIFY,
        "notify_by": UserNotificationPolicy.NotificationChannel.SLACK,
        "wait_delay": None,
        "important": False,
        "user": user.public_primary_key,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_user_cant_create_notification_policy_for_user(
    user_notification_policy_internal_api_setup,
    make_user_auth_headers,
):
    token, _, users = user_notification_policy_internal_api_setup
    admin, user = users

    client = APIClient()
    url = reverse("api-internal:notification_policy-list")

    data = {
        "step": UserNotificationPolicy.Step.NOTIFY,
        "notify_by": UserNotificationPolicy.NotificationChannel.SLACK,
        "wait_delay": None,
        "important": False,
        "user": admin.public_primary_key,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_create_notification_policy_order_is_ignored(
    user_notification_policy_internal_api_setup,
    make_user_auth_headers,
):
    token, steps, users = user_notification_policy_internal_api_setup
    wait_notification_step, _, _, _ = steps
    admin, _ = users
    client = APIClient()
    url = reverse("api-internal:notification_policy-list")

    data = {
        "position": 2023,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "notify_by": UserNotificationPolicy.NotificationChannel.SLACK,
        "wait_delay": None,
        "important": False,
        "user": admin.public_primary_key,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["order"] == 2


@pytest.mark.django_db
def test_move_to_position_position_error(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    admin, _ = users
    step = steps[0]
    client = APIClient()
    url = reverse("api-internal:notification_policy-move-to-position", kwargs={"pk": step.public_primary_key})

    # position value only can be 0 or 1 for this test setup, because there are only 2 steps
    response = client.put(f"{url}?position=2", content_type="application/json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_step(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    admin, _ = users

    _, notify_notification_step, _, _ = steps
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": notify_notification_step.public_primary_key})

    response = client.patch(
        url,
        data=json.dumps({"notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL}),
        content_type="application/json",
        **make_user_auth_headers(admin, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["notify_by"] == UserNotificationPolicy.NotificationChannel.PHONE_CALL


@pytest.mark.django_db
def test_admin_can_update_user_step(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    admin, _ = users
    _, _, _, second_user_step = steps
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": second_user_step.public_primary_key})

    response = client.patch(
        url,
        data=json.dumps({"notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL}),
        content_type="application/json",
        **make_user_auth_headers(admin, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["notify_by"] == UserNotificationPolicy.NotificationChannel.PHONE_CALL


@pytest.mark.django_db
def test_user_cant_update_admin_step(
    user_notification_policy_internal_api_setup,
    make_user_auth_headers,
):
    token, steps, users = user_notification_policy_internal_api_setup
    _, user = users

    admin_step, _, _, _ = steps
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": admin_step.public_primary_key})

    response = client.patch(
        url,
        data=json.dumps({"notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_move_user_step(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    admin, _ = users
    _, _, _, second_user_step = steps
    client = APIClient()
    url = reverse(
        "api-internal:notification_policy-move-to-position", kwargs={"pk": second_user_step.public_primary_key}
    )

    response = client.put(f"{url}?position=0", content_type="application/json", **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_cant_move_admin_step(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    _, user = users

    admin_step, _, _, _ = steps
    client = APIClient()
    url = reverse("api-internal:notification_policy-move-to-position", kwargs={"pk": admin_step.public_primary_key})

    response = client.put(f"{url}?position=1", content_type="application/json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_unable_to_change_importance(user_notification_policy_internal_api_setup, make_user_auth_headers):
    token, steps, users = user_notification_policy_internal_api_setup
    admin, _ = users
    _, notify_notification_step, _, _ = steps
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": notify_notification_step.public_primary_key})

    data = {
        "important": True,
    }
    response = client.patch(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(admin, token)
    )
    notify_notification_step.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert notify_notification_step.important != data["important"]


@pytest.mark.django_db
@pytest.mark.parametrize("wait_delay, expected_wait_delay", [(None, "300.0"), ("900.0", "900.0")])
def test_switch_step_type_from_notify_to_wait(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_notification_policy,
    wait_delay,
    expected_wait_delay,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()

    notify_notification_step = make_user_notification_policy(
        admin,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
        important=False,
    )
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": notify_notification_step.public_primary_key})

    data = {
        "id": notify_notification_step.public_primary_key,
        "important": False,
        "notify_by": None,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.WAIT,
        "wait_delay": wait_delay,
    }

    expected_response = {
        "id": notify_notification_step.public_primary_key,
        "important": False,
        "notify_by": None,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.WAIT,
        "wait_delay": expected_wait_delay,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(admin, token)
    )
    notify_notification_step.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
@pytest.mark.parametrize(
    "notification_channel, expected_notification_channel",
    [
        (None, DEFAULT_NOTIFICATION_CHANNEL),
        (
            UserNotificationPolicy.NotificationChannel.PHONE_CALL,
            UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        ),
    ],
)
def test_switch_step_type_wait_to_notify(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_notification_policy,
    notification_channel,
    expected_notification_channel,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()

    wait_notification_step = make_user_notification_policy(
        admin,
        UserNotificationPolicy.Step.WAIT,
        important=False,
    )

    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": wait_notification_step.public_primary_key})

    data = {
        "id": wait_notification_step.public_primary_key,
        "important": False,
        "notify_by": notification_channel,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": None,
    }

    expected_response = {
        "id": wait_notification_step.public_primary_key,
        "important": False,
        "notify_by": expected_notification_channel,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(admin, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_switch_notification_channel(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_notification_policy,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()

    notify_notification_step = make_user_notification_policy(
        admin,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
        important=False,
    )
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": notify_notification_step.public_primary_key})

    data = {
        "id": notify_notification_step.public_primary_key,
        "important": False,
        "notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": None,
    }

    expected_response = {
        "id": notify_notification_step.public_primary_key,
        "important": False,
        "notify_by": UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(admin, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
@pytest.mark.parametrize(
    "from_wait_delay, to_wait_delay", [(None, "300.0"), (timezone.timedelta(seconds=900), "900.0")]
)
def test_switch_wait_delay(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_user_notification_policy,
    from_wait_delay,
    to_wait_delay,
):
    organization, admin, token = make_organization_and_user_with_plugin_token()
    wait_notification_step = make_user_notification_policy(
        admin, UserNotificationPolicy.Step.WAIT, wait_delay=from_wait_delay, important=False
    )
    client = APIClient()
    url = reverse("api-internal:notification_policy-detail", kwargs={"pk": wait_notification_step.public_primary_key})

    data = {
        "id": wait_notification_step.public_primary_key,
        "important": False,
        "notify_by": DEFAULT_NOTIFICATION_CHANNEL,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": to_wait_delay,
    }

    expected_response = {
        "id": wait_notification_step.public_primary_key,
        "important": False,
        "notify_by": DEFAULT_NOTIFICATION_CHANNEL,
        "order": 0,
        "user": admin.public_primary_key,
        "step": UserNotificationPolicy.Step.NOTIFY,
        "wait_delay": to_wait_delay,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(admin, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_notification_policy_backends_enabled(
    user_notification_policy_internal_api_setup, settings, make_user_auth_headers
):
    token, _, users = user_notification_policy_internal_api_setup
    admin, _ = users

    client = APIClient()
    url = reverse("api-internal:notification_policy-notify-by-options")

    response = client.get(url, **make_user_auth_headers(admin, token))
    assert response.status_code == status.HTTP_200_OK
    options = [opt["display_name"] for opt in response.json()]
    assert "Test Only Backend" in options


@pytest.mark.django_db
def test_notification_policy_backends_disabled_for_organization(
    user_notification_policy_internal_api_setup, settings, make_user_auth_headers
):
    token, _, users = user_notification_policy_internal_api_setup
    admin, _ = users

    client = APIClient()
    url = reverse("api-internal:notification_policy-notify-by-options")

    with patch.object(TestOnlyBackend, "is_enabled_for_organization", return_value=False):
        response = client.get(url, **make_user_auth_headers(admin, token))

    assert response.status_code == status.HTTP_200_OK

    options = [opt["display_name"] for opt in response.json()]
    assert "Test Only Backend" not in options
