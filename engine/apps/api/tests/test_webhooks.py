import json
from unittest import mock
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.webhooks.models import Webhook

TEST_URL = "https://some-url"


@pytest.fixture()
def webhook_internal_api_setup(make_organization_and_user_with_plugin_token, make_custom_webhook):
    organization, user, token = make_organization_and_user_with_plugin_token()
    webhook = make_custom_webhook(
        name="some_webhook",
        url="https://github.com/",
        username="Chris Vanstras",
        password="qwerty",
        data='{"name": "{{ alert_payload }}"}',
        authorization_header="auth_token",
        organization=organization,
        forward_all=False,
    )
    return user, token, webhook


@pytest.mark.django_db
def test_get_list_webhooks(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    expected_payload = [
        {
            "id": webhook.public_primary_key,
            "name": "some_webhook",
            "team": None,
            "url": "https://github.com/",
            "data": '{"name": "{{ alert_payload }}"}',
            "username": "Chris Vanstras",
            "forward_all": False,
            "headers": None,
            "http_method": "POST",
            "last_run": "",
            "last_status_log": {
                "data": "",
                "headers": "",
                "input_data": None,
                "last_run_at": None,
                "response": "",
                "response_status": "",
                "trigger": "",
                "url": "",
            },
            "trigger_template": None,
            "trigger_type": None,
            "trigger_type_name": "",
        }
    ]

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_detail_webhook(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    expected_payload = {
        "id": webhook.public_primary_key,
        "name": "some_webhook",
        "team": None,
        "url": "https://github.com/",
        "data": '{"name": "{{ alert_payload }}"}',
        "username": "Chris Vanstras",
        "forward_all": False,
        "headers": None,
        "http_method": "POST",
        "last_run": "",
        "last_status_log": {
            "data": "",
            "headers": "",
            "input_data": None,
            "last_run_at": None,
            "response": "",
            "response_status": "",
            "trigger": "",
            "url": "",
        },
        "trigger_template": None,
        "trigger_type": None,
        "trigger_type_name": "",
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@mock.patch("apps.api.views.webhooks.WebhooksView.check_webhooks_2_enabled")
@pytest.mark.django_db
def test_create_webhook(mocked_check_webhooks_2_enabled, webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": str(Webhook.TRIGGER_NEW),
        "team": None,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    webhook = Webhook.objects.get(public_primary_key=response.json()["id"])
    expected_response = data | {
        "id": webhook.public_primary_key,
        "data": None,
        "username": None,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "last_run": "",
        "last_status_log": {
            "data": "",
            "headers": "",
            "input_data": None,
            "last_run_at": None,
            "response": "",
            "response_status": "",
            "trigger": "",
            "url": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Triggered",
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response
    # user creating the webhook is set
    assert webhook.user == user


@mock.patch("apps.api.views.webhooks.WebhooksView.check_webhooks_2_enabled")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name,value",
    [
        ("data", '{"name": "{{ alert_payload }}"}'),
        ("headers", '"request-id": "{{ alert_payload.id }}"'),
        ("trigger_template", "integration_id == {{ some_var_value }}"),
        ("url", "https://myserver/{{ alert_payload.id }}/triggered"),
    ],
)
def test_create_valid_templated_field(
    mocked_check_webhooks_2_enabled, webhook_internal_api_setup, make_user_auth_headers, field_name, value
):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "webhook_with_valid_data",
        "url": TEST_URL,
        field_name: value,
        "trigger_type": str(Webhook.TRIGGER_NEW),
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": webhook.public_primary_key,
        "username": None,
        "forward_all": True,
        "headers": None,
        "data": None,
        "http_method": "POST",
        "last_run": "",
        "last_status_log": {
            "data": "",
            "headers": "",
            "input_data": None,
            "last_run_at": None,
            "response": "",
            "response_status": "",
            "trigger": "",
            "url": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Triggered",
    }
    # update expected value for changed field
    expected_response[field_name] = value
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@mock.patch("apps.api.views.webhooks.WebhooksView.check_webhooks_2_enabled")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name,value",
    [
        ("data", "{{%"),
        ("headers", '"request-id": "{{}}"'),
        ("trigger_template", "integration_id == {{}}"),
        ("url", "invalid-url/{{}}/triggered"),
    ],
)
def test_create_invalid_templated_field(
    mocked_check_webhooks_2_enabled, webhook_internal_api_setup, make_user_auth_headers, field_name, value
):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "webhook_with_valid_data",
        "url": TEST_URL,
        field_name: value,
        "trigger_type": str(Webhook.TRIGGER_NEW),
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@mock.patch("apps.api.views.webhooks.WebhooksView.check_webhooks_2_enabled")
@pytest.mark.django_db
def test_update_webhook(mocked_check_webhooks_2_enabled, webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    data = {
        "name": "github_button_updated",
        "url": "https://github.com/",
        "trigger_type": str(Webhook.TRIGGER_NEW),
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = Webhook.objects.get(public_primary_key=webhook.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "github_button_updated"


@mock.patch("apps.api.views.webhooks.WebhooksView.check_webhooks_2_enabled")
@pytest.mark.django_db
def test_delete_webhook(mocked_check_webhooks_2_enabled, webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_webhook_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:webhooks-list")

    with patch(
        "apps.api.views.webhooks.WebhooksView.create",
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
def test_webhook_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_webhook,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    webhook = make_custom_webhook(organization=organization)
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    with patch(
        "apps.api.views.webhooks.WebhooksView.update",
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
def test_webhook_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_webhook,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    make_custom_webhook(organization=organization)
    client = APIClient()

    url = reverse("api-internal:webhooks-list")

    with patch(
        "apps.api.views.webhooks.WebhooksView.list",
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
def test_webhook_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_webhook,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    webhook = make_custom_webhook(organization=organization)
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    with patch(
        "apps.api.views.webhooks.WebhooksView.retrieve",
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
def test_webhook_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_webhook,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    webhook = make_custom_webhook(organization=organization)
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    with patch(
        "apps.api.views.webhooks.WebhooksView.destroy",
        return_value=Response(
            status=status.HTTP_204_NO_CONTENT,
        ),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_get_webhook_from_other_team_with_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    webhook = make_custom_webhook(organization=organization, team=team)
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    url = f"{url}?from_organization=true"

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_webhook_from_other_team_without_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    webhook = make_custom_webhook(organization=organization, team=team)
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN
