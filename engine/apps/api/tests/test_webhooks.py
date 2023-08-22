import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.api.views.webhooks import RECENT_RESPONSE_LIMIT, WEBHOOK_URL
from apps.webhooks.models import Webhook
from apps.webhooks.models.webhook import WEBHOOK_FIELD_PLACEHOLDER

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
            "password": WEBHOOK_FIELD_PLACEHOLDER,
            "authorization_header": WEBHOOK_FIELD_PLACEHOLDER,
            "forward_all": False,
            "headers": None,
            "http_method": "POST",
            "integration_filter": None,
            "is_webhook_enabled": True,
            "is_legacy": False,
            "last_response_log": {
                "request_data": "",
                "request_headers": "",
                "timestamp": None,
                "content": "",
                "status_code": None,
                "request_trigger": "",
                "url": "",
                "event_data": "",
            },
            "trigger_template": None,
            "trigger_type": "0",
            "trigger_type_name": "Escalation step",
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
        "password": WEBHOOK_FIELD_PLACEHOLDER,
        "authorization_header": WEBHOOK_FIELD_PLACEHOLDER,
        "forward_all": False,
        "headers": None,
        "http_method": "POST",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type": "0",
        "trigger_type_name": "Escalation step",
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_create_webhook(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    webhook = Webhook.objects.get(public_primary_key=response.json()["id"])
    expected_response = data | {
        "id": webhook.public_primary_key,
        "data": None,
        "username": None,
        "password": None,
        "authorization_header": None,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Alert Group Created",
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response
    # user creating the webhook is set
    assert webhook.user == user


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
def test_create_valid_templated_field(webhook_internal_api_setup, make_user_auth_headers, field_name, value):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "webhook_with_valid_data",
        "url": TEST_URL,
        field_name: value,
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": webhook.public_primary_key,
        "username": None,
        "password": None,
        "authorization_header": None,
        "forward_all": True,
        "headers": None,
        "data": None,
        "http_method": "POST",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Alert Group Created",
    }
    # update expected value for changed field
    expected_response[field_name] = value
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


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
def test_create_invalid_templated_field(webhook_internal_api_setup, make_user_auth_headers, field_name, value):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "webhook_with_valid_data",
        "url": TEST_URL,
        field_name: value,
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_webhook(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    data = {
        "name": "github_button_updated",
        "url": "https://github.com/",
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = Webhook.objects.get(public_primary_key=webhook.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "github_button_updated"


@pytest.mark.django_db
def test_delete_webhook(webhook_internal_api_setup, make_user_auth_headers):
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
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_webhook_responses(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_custom_webhook,
    make_webhook_response,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    webhook = make_custom_webhook(
        organization=organization, team=team, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED
    )
    for i in range(0, RECENT_RESPONSE_LIMIT + 1):
        make_webhook_response(
            webhook=webhook,
            trigger_type=webhook.trigger_type,
            status_code=200,
            content=json.dumps({"id": "third-party-id"}),
            event_data=json.dumps({"test": f"{i}"}),
        )

    client = APIClient()
    url = reverse("api-internal:webhooks-responses", kwargs={"pk": webhook.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == RECENT_RESPONSE_LIMIT


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_template, test_payload, expected_result",
    [
        ("https://test.com", None, "https://test.com"),
        ("https://test.com", "", "https://test.com"),
        ("{{ name }}", {"name": "test_1"}, "test_1"),
        ("{{ name }}", '{"name": "test_1"}', "test_1"),
    ],
)
def test_webhook_preview_template(
    webhook_internal_api_setup, make_user_auth_headers, test_template, test_payload, expected_result
):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-preview-template", kwargs={"pk": webhook.public_primary_key})
    data = {
        "template_name": WEBHOOK_URL,
        "template_body": test_template,
        "payload": test_payload,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["preview"] == expected_result


@pytest.mark.django_db
def test_webhook_field_masking(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
        "password": "secret_password",
        "authorization_header": "auth 1234",
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])

    expected_response = data | {
        "id": webhook.public_primary_key,
        "data": None,
        "username": None,
        "password": WEBHOOK_FIELD_PLACEHOLDER,
        "authorization_header": WEBHOOK_FIELD_PLACEHOLDER,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Alert Group Created",
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response
    assert webhook.password == data["password"]
    assert webhook.authorization_header == data["authorization_header"]
    assert webhook.user == user


@pytest.mark.django_db
def test_webhook_copy(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": str(Webhook.TRIGGER_ALERT_GROUP_CREATED),
        "team": None,
        "password": "secret_password",
        "authorization_header": "auth 1234",
    }
    response1 = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    get_url = reverse("api-internal:webhooks-detail", kwargs={"pk": response1.data["id"]})
    response2 = client.get(get_url, format="json", **make_user_auth_headers(user, token))
    to_copy = response2.json()
    to_copy["name"] = "copied_webhook"
    response3 = client.post(url, to_copy, format="json", **make_user_auth_headers(user, token))
    webhook = Webhook.objects.get(public_primary_key=response3.data["id"])

    expected_response = data | {
        "id": webhook.public_primary_key,
        "name": to_copy["name"],
        "data": None,
        "username": None,
        "password": WEBHOOK_FIELD_PLACEHOLDER,
        "authorization_header": WEBHOOK_FIELD_PLACEHOLDER,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type_name": "Alert Group Created",
    }

    assert response3.status_code == status.HTTP_201_CREATED
    assert response3.json() == expected_response
    assert webhook.password == data["password"]
    assert webhook.authorization_header == data["authorization_header"]
    assert webhook.id != to_copy["id"]
    assert webhook.user == user
