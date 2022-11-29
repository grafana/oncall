from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_channel_filter_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:channel_filter-list")

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.create",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

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
def test_channel_filter_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.update",
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_channel_filter_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-list")

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.list",
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_channel_filter_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.retrieve",
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_channel_filter_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.destroy",
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_channel_filter_move_to_position_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-move-to-position", kwargs={"pk": channel_filter.public_primary_key})

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.move_to_position",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

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
def test_alert_receive_channel_send_demo_alert_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_channel_filter,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    client = APIClient()

    url = reverse("api-internal:channel_filter-send-demo-alert", kwargs={"pk": channel_filter.public_primary_key})

    with patch(
        "apps.api.views.channel_filter.ChannelFilterView.send_demo_alert",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_channel_filter_create_with_order(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_escalation_chain(organization)
    # create default channel filter
    make_channel_filter(alert_receive_channel, is_default=True)
    channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False)
    client = APIClient()

    url = reverse("api-internal:channel_filter-list")
    data_for_creation = {
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "filtering_term": "b",
        "order": 0,
    }

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))
    channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["order"] == 0
    assert channel_filter.order == 1


@pytest.mark.django_db
def test_channel_filter_create_without_order(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_escalation_chain(organization)
    make_channel_filter(alert_receive_channel, is_default=True)
    channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False)
    client = APIClient()

    url = reverse("api-internal:channel_filter-list")
    data_for_creation = {
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "filtering_term": "b",
    }

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))
    channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["order"] == 1
    assert channel_filter.order == 0


@pytest.mark.django_db
def test_channel_filter_update_with_order(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    # create default channel filter
    make_channel_filter(alert_receive_channel, is_default=True)
    first_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False)
    second_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="b", is_default=False)

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": first_channel_filter.public_primary_key})
    data_for_update = {
        "id": first_channel_filter.public_primary_key,
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "order": 1,
        "filtering_term": first_channel_filter.filtering_term,
    }

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    first_channel_filter.refresh_from_db()
    second_channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order"] == 1
    assert first_channel_filter.order == 1
    assert second_channel_filter.order == 0


@pytest.mark.django_db
def test_channel_filter_update_without_order(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    # create default channel filter
    make_channel_filter(alert_receive_channel, is_default=True)
    first_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False)
    second_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="b", is_default=False)

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": first_channel_filter.public_primary_key})
    data_for_update = {
        "id": first_channel_filter.public_primary_key,
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "filtering_term": first_channel_filter.filtering_term + "_updated",
    }

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    first_channel_filter.refresh_from_db()
    second_channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order"] == 0
    assert first_channel_filter.order == 0
    assert second_channel_filter.order == 1


@pytest.mark.django_db
def test_channel_filter_notification_backends(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    extra_notification_backends = {"TESTONLY": {"channel_id": "abc123"}}
    channel_filter = make_channel_filter(
        alert_receive_channel,
        notification_backends=extra_notification_backends,
    )

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["notification_backends"] == extra_notification_backends


@pytest.mark.django_db
def test_channel_filter_update_notification_backends(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    extra_notification_backends = {"TESTONLY": {"channel_id": "abc123"}}
    channel_filter = make_channel_filter(alert_receive_channel)

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})
    data_for_update = {
        "notification_backends": extra_notification_backends,
    }

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["notification_backends"] == extra_notification_backends
    assert channel_filter.notification_backends == extra_notification_backends


@pytest.mark.django_db
def test_channel_filter_update_notification_backends_updates_existing_data(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    existing_notification_backends = {
        "TESTONLY": {"enabled": True, "channel": "ABCDEF"},
        "ANOTHERONE": {"enabled": False, "channel": "123456"},
    }
    channel_filter = make_channel_filter(alert_receive_channel, notification_backends=existing_notification_backends)

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})
    notification_backends_update = {"TESTONLY": {"channel": "abc123"}}
    data_for_update = {
        "notification_backends": notification_backends_update,
    }

    class FakeBackend:
        def validate_channel_filter_data(self, organization, data):
            return data

    with patch("apps.api.serializers.channel_filter.get_messaging_backend_from_id") as mock_get_backend:
        mock_get_backend.return_value = FakeBackend()
        response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    channel_filter.refresh_from_db()

    expected_notification_backends = existing_notification_backends
    for backend, updated_data in notification_backends_update.items():
        expected_notification_backends[backend] = expected_notification_backends.get(backend, {}) | updated_data
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["notification_backends"] == expected_notification_backends
    assert channel_filter.notification_backends == expected_notification_backends


@pytest.mark.django_db
def test_channel_filter_update_invalid_notification_backends(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    extra_notification_backends = {"INVALID": {"channel_id": "abc123"}}
    channel_filter = make_channel_filter(alert_receive_channel)

    client = APIClient()

    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": channel_filter.public_primary_key})
    data_for_update = {
        "notification_backends": extra_notification_backends,
    }

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    channel_filter.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"notification_backends": ["Invalid messaging backend"]}
    assert channel_filter.notification_backends is None
