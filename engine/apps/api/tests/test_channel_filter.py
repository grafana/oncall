from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import ChannelFilter
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
def test_channel_filter_create_order(
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

    # check that orders are correct
    assert ChannelFilter.objects.get(public_primary_key=response.json()["id"]).order == 0
    assert channel_filter.order == 1


@pytest.mark.django_db
def test_move_to_position(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    # create default channel filter
    make_channel_filter(alert_receive_channel, is_default=True, order=0)
    first_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False, order=1)
    second_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="b", is_default=False, order=2)

    client = APIClient()
    url = reverse(
        "api-internal:channel_filter-move-to-position", kwargs={"pk": first_channel_filter.public_primary_key}
    )
    url += "?position=1"
    response = client.put(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    first_channel_filter.refresh_from_db()
    second_channel_filter.refresh_from_db()
    assert first_channel_filter.order == 2
    assert second_channel_filter.order == 1


@pytest.mark.django_db
def test_move_to_position_invalid_index(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    # create default channel filter
    make_channel_filter(alert_receive_channel, is_default=True, order=0)
    first_channel_filter = make_channel_filter(alert_receive_channel, filtering_term="a", is_default=False, order=1)
    make_channel_filter(alert_receive_channel, filtering_term="b", is_default=False, order=2)

    client = APIClient()
    url = reverse(
        "api-internal:channel_filter-move-to-position", kwargs={"pk": first_channel_filter.public_primary_key}
    )
    url += "?position=2"
    response = client.put(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_move_to_position_cant_move_default(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    # create default channel filter
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True, order=0)
    make_channel_filter(alert_receive_channel, filtering_term="b", is_default=False, order=1)

    client = APIClient()
    url = reverse(
        "api-internal:channel_filter-move-to-position", kwargs={"pk": default_channel_filter.public_primary_key}
    )
    url += "?position=1"
    response = client.put(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_channel_filter_update(
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_channel_filter_convert_from_regex_to_jinja2(
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

    # r"..." used to keep this string as raw string
    regex_filtering_term = r"\".*\": \"This alert was sent by user for demonstration purposes\""
    final_filtering_term = r'{{ payload | json_dumps | regex_search("\".*\": \"This alert was sent by user for demonstration purposes\"") }}'
    payload = {"description": "This alert was sent by user for demonstration purposes"}

    regex_channel_filter = make_channel_filter(
        alert_receive_channel,
        filtering_term=regex_filtering_term,
        is_default=False,
    )
    # Check if the filtering term is a regex
    assert regex_channel_filter.filtering_term_type == regex_channel_filter.FILTERING_TERM_TYPE_REGEX
    # Check if the alert is matched to the channel filter (route) regex
    assert bool(regex_channel_filter.is_satisfying(payload)) is True

    client = APIClient()
    url = reverse("api-internal:channel_filter-detail", kwargs={"pk": regex_channel_filter.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    # Check if preview of the filtering term migration is correct
    assert response.json()["filtering_term_as_jinja2"] == final_filtering_term

    url = reverse(
        "api-internal:channel_filter-convert-from-regex-to-jinja2",
        kwargs={"pk": regex_channel_filter.public_primary_key},
    )
    response = client.post(url, **make_user_auth_headers(user, token))
    # Only admins can convert from regex to jinja2
    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        regex_channel_filter.refresh_from_db()
        # Regex is now converted to jinja2
        jinja2_channel_filter = regex_channel_filter
        # Check if the filtering term is a jinja2, and if it is correct
        assert jinja2_channel_filter.filtering_term_type == jinja2_channel_filter.FILTERING_TERM_TYPE_JINJA2
        assert jinja2_channel_filter.filtering_term == final_filtering_term
        # Check if the same alert is matched to the channel filter (route) new jinja2
        assert bool(jinja2_channel_filter.is_satisfying(payload)) is True
