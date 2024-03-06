from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@patch(
    "apps.labels.client.LabelsAPIClient.get_keys",
    return_value=([{"name": "team", "id": "keyid123"}], MockResponse(status_code=200)),
)
@pytest.mark.django_db
def test_labels_get_keys(
    mocked_get_labels_keys,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_keys")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = [{"name": "team", "id": "keyid123"}]

    assert mocked_get_labels_keys.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.get_label_by_key_id",
    return_value=(
        {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]},
        MockResponse(status_code=200),
    ),
)
@pytest.mark.django_db
def test_get_update_key_get(
    mocked_get_label_by_key_id,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]}

    assert mocked_get_label_by_key_id.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.rename_key",
    return_value=(
        {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]},
        MockResponse(status_code=200),
    ),
)
@pytest.mark.django_db
def test_get_update_key_put(
    mocked_rename_key,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    data = {"name": "team"}
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]}

    assert mocked_rename_key.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.add_value",
    return_value=(
        {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]},
        MockResponse(status_code=200),
    ),
)
@pytest.mark.django_db
def test_add_value(
    mocked_add_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:add_value", kwargs={"key_id": "keyid123"})
    data = {"name": "yolo"}
    response = client.post(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]}

    assert mocked_add_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.rename_value",
    return_value=(
        {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]},
        MockResponse(status_code=200),
    ),
)
@pytest.mark.django_db
def test_rename_value(
    mocked_rename_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    data = {"name": "yolo"}
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]}

    assert mocked_rename_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.get_value",
    return_value=(
        {"id": "valueid123", "name": "yolo"},
        MockResponse(status_code=200),
    ),
)
@pytest.mark.django_db
def test_get_value(
    mocked_get_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = {"id": "valueid123", "name": "yolo"}

    assert mocked_get_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.create_label",
    return_value=(
        {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]},
        MockResponse(status_code=201),
    ),
)
@pytest.mark.django_db
def test_labels_create_label(
    mocked_create_label,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:create_label")
    data = {"key": {"name": "team"}, "values": [{"name": "yolo"}]}
    expected_result = {"key": {"id": "keyid123", "name": "team"}, "values": [{"id": "valueid123", "name": "yolo"}]}
    response = client.post(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert mocked_create_label.called
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_result


@pytest.mark.django_db
def test_labels_feature_false(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    settings,
):
    settings.FEATURE_LABELS_ENABLED_FOR_ALL = False

    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:get_keys")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data={})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:add_value", kwargs={"key_id": "keyid123"})
    response = client.post(url, format="json", **make_user_auth_headers(user, token), data={})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data={})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:create_label")
    response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_labels_permissions_get_actions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    with patch("apps.api.views.labels.LabelsViewSet.get_keys", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:get_keys")
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == expected_status

    with patch("apps.api.views.labels.LabelsViewSet.get_key", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == expected_status

    with patch("apps.api.views.labels.LabelsViewSet.get_value", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
        response = client.get(url, format="json", **make_user_auth_headers(user, token), data={})
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_labels_permissions_create_update_actions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    with patch("apps.api.views.labels.LabelsViewSet.rename_key", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
        response = client.put(url, format="json", **make_user_auth_headers(user, token), data={})
        assert response.status_code == expected_status

    with patch("apps.api.views.labels.LabelsViewSet.add_value", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:add_value", kwargs={"key_id": "keyid123"})
        response = client.post(url, format="json", **make_user_auth_headers(user, token), data={})
        assert response.status_code == expected_status

    with patch("apps.api.views.labels.LabelsViewSet.rename_value", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
        response = client.put(url, format="json", **make_user_auth_headers(user, token), data={})
        assert response.status_code == expected_status

    with patch("apps.api.views.labels.LabelsViewSet.create_label", return_value=Response(status=status.HTTP_200_OK)):
        url = reverse("api-internal:create_label")
        response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
        assert response.status_code == expected_status


@pytest.mark.django_db
def test_alert_group_labels_get_keys(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_alert_group,
    make_alert_group_label_association,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(user.organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert_group_label_association(organization, alert_group, key_name="a", value_name="b")

    client = APIClient()
    url = reverse("api-internal:alert_group_labels-get_keys")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": "a", "name": "a"}]


@pytest.mark.django_db
def test_alert_group_labels_get_key(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_alert_group,
    make_alert_group_label_association,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(user.organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert_group_label_association(organization, alert_group, key_name="a", value_name="b")

    client = APIClient()
    url = reverse("api-internal:alert_group_labels-get_key", kwargs={"key_id": "a"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"key": {"id": "a", "name": "a"}, "values": [{"id": "b", "name": "b"}]}
