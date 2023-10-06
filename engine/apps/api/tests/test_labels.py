from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@patch(
    "apps.labels.client.LabelsAPIClient.get_keys",
    return_value=([{"repr": "team", "id": "keyid123"}], {"status_code": status.HTTP_200_OK}),
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
    expected_result = [{"repr": "team", "id": "keyid123"}]

    assert mocked_get_labels_keys.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.get_values",
    return_value=(
        {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
        {"status_code": status.HTTP_200_OK},
    ),
)
@pytest.mark.django_db
def test_get_update_key_get(
    mocked_get_values,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}

    assert mocked_get_values.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.rename_key",
    return_value=(
        {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
        {"status_code": status.HTTP_200_OK},
    ),
)
@pytest.mark.django_db
def test_get_update_key_put(
    mocked_rename_key,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_key", kwargs={"key_id": "keyid123"})
    data = {"repr": "team"}
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}

    assert mocked_rename_key.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.add_value",
    return_value=(
        {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
        {"status_code": status.HTTP_200_OK},
    ),
)
@pytest.mark.django_db
def test_add_value(
    mocked_add_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:add_value", kwargs={"key_id": "keyid123"})
    data = {"repr": "yolo"}
    response = client.post(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}

    assert mocked_add_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.rename_value",
    return_value=(
        {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
        {"status_code": status.HTTP_200_OK},
    ),
)
@pytest.mark.django_db
def test_rename_value(
    mocked_rename_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    data = {"repr": "yolo"}
    response = client.put(url, format="json", **make_user_auth_headers(user, token), data=data)
    expected_result = {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}

    assert mocked_rename_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.get_value",
    return_value=(
        {"id": "valueid123", "repr": "yolo"},
        {"status_code": status.HTTP_200_OK},
    ),
)
@pytest.mark.django_db
def test_get_value(
    mocked_get_value,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:get_update_value", kwargs={"key_id": "keyid123", "value_id": "valueid123"})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = {"id": "valueid123", "repr": "yolo"}

    assert mocked_get_value.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@patch(
    "apps.labels.client.LabelsAPIClient.create_label",
    return_value=(
        {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
        {"status_code": status.HTTP_201_CREATED},
    ),
)
@pytest.mark.django_db
def test_labels_create_label(
    mocked_create_label,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:create_label")
    data = {"key": {"repr": "team"}, "values": [{"repr": "yolo"}]}
    expected_result = {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}
    response = client.post(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert mocked_create_label.called
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_result
