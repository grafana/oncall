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
def test_get_list_webhooks(webhook_internal_api_setup, make_custom_webhook, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    # connected integration webhooks are not included
    make_custom_webhook(organization=user.organization, is_from_connected_integration=True)

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
            "integration_filter": [],
            "is_webhook_enabled": True,
            "labels": [],
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
            "preset": None,
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
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "preset": None,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_detail_connected_integration_webhook(
    webhook_internal_api_setup, make_custom_webhook, make_user_auth_headers
):
    user, token, _ = webhook_internal_api_setup
    # it is possible to get details for a connected integration webhook
    webhook = make_custom_webhook(organization=user.organization, is_from_connected_integration=True)

    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    expected_payload = {
        "id": webhook.public_primary_key,
        "name": webhook.name,
        "team": None,
        "url": webhook.url,
        "data": webhook.data,
        "username": None,
        "password": None,
        "authorization_header": None,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "preset": None,
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
        "preset": None,
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
        "preset": None,
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
def test_webhook_integration_filter(webhook_internal_api_setup, make_alert_receive_channel, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    alert_receive_channel_1 = make_alert_receive_channel(user.organization)
    alert_receive_channel_2 = make_alert_receive_channel(user.organization)

    client = APIClient()

    # create webhook setting integrations filter
    url = reverse("api-internal:webhooks-list")
    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
        "team": None,
        "integration_filter": [alert_receive_channel_1.public_primary_key],
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED
    webhook = Webhook.objects.get(public_primary_key=response.json()["id"])
    assert list(webhook.filtered_integrations.all()) == [alert_receive_channel_1]
    assert response.json()["integration_filter"] == [alert_receive_channel_1.public_primary_key]

    # update filter
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {
        "name": "github_button_updated",
        "url": "https://github.com/",
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
        "team": None,
        "integration_filter": [alert_receive_channel_1.public_primary_key, alert_receive_channel_2.public_primary_key],
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    webhook.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert list(webhook.filtered_integrations.all()) == [alert_receive_channel_1, alert_receive_channel_2]
    assert response.json()["integration_filter"] == [
        alert_receive_channel_1.public_primary_key,
        alert_receive_channel_2.public_primary_key,
    ]

    # clear filter
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {
        "name": "github_button_updated",
        "url": "https://github.com/",
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
        "team": None,
        "integration_filter": [],
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    webhook.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert list(webhook.filtered_integrations.all()) == []
    assert response.json()["integration_filter"] == []

    # clear filter also works if set to None
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {
        "name": "github_button_updated",
        "url": "https://github.com/",
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
        "team": None,
        "integration_filter": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    webhook.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert list(webhook.filtered_integrations.all()) == []
    assert response.json()["integration_filter"] == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
        "preset": None,
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
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
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
        "integration_filter": [],
        "is_webhook_enabled": True,
        "labels": [],
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
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
        "preset": None,
    }

    assert response3.status_code == status.HTTP_201_CREATED
    assert response3.json() == expected_response
    assert webhook.password == data["password"]
    assert webhook.authorization_header == data["authorization_header"]
    assert webhook.id != to_copy["id"]
    assert webhook.user == user


@pytest.mark.django_db
def test_create_invalid_missing_fields(webhook_internal_api_setup, make_user_auth_headers):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {"url": TEST_URL, "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED, "http_method": "POST"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["name"][0] == "This field is required."

    data = {"name": "test webhook 1", "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED, "http_method": "POST"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["url"][0] == "This field is required."

    data = {"name": "test webhook 2", "url": TEST_URL, "http_method": "POST"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["trigger_type"][0] == "This field is required."

    data = {
        "name": "test webhook 3",
        "url": TEST_URL,
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["http_method"][0]
        == "This field must be one of ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']."
    )

    data = {
        "name": "test webhook 3",
        "url": TEST_URL,
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "TOAST",
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["http_method"][0]
        == "This field must be one of ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']."
    )

    data = {"name": "test webhook 3", "url": TEST_URL, "trigger_type": 2000000, "http_method": "POST"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["trigger_type"][0] == "This field is required."


@pytest.mark.django_db
def test_webhook_filter_by_labels(
    make_organization_and_user_with_plugin_token,
    make_custom_webhook,
    make_webhook_label_association,
    make_label_key_and_value,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    webhook_with_label = make_custom_webhook(organization)
    label = make_webhook_label_association(organization, webhook_with_label)

    webhook_with_another_label = make_custom_webhook(organization)
    another_label = make_webhook_label_association(organization, webhook_with_another_label)

    not_attached_key, not_attached_value = make_label_key_and_value(organization)

    client = APIClient()

    # test filter by label, which is attached to only one webhook
    url = reverse("api-internal:webhooks-list")
    response = client.get(
        f"{url}?label={label.key_id}:{label.value_id}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == webhook_with_label.public_primary_key

    url = reverse("api-internal:webhooks-list")
    response = client.get(
        f"{url}?label={another_label.key_id}:{another_label.value_id}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == webhook_with_another_label.public_primary_key

    # test filter by label which is not attached to any webhooks
    response = client.get(
        f"{url}?label={not_attached_key.id}:{not_attached_value.id}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert len(response.json()) == 0


@pytest.mark.django_db
def test_update_webhook_labels(
    webhook_internal_api_setup,
    make_user_auth_headers,
):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    key_id = "testkey"
    value_id = "testvalue"
    data = {
        "labels": [
            {
                "key": {"id": key_id, "name": "test", "prescribed": False},
                "value": {"id": value_id, "name": "testv", "prescribed": False},
            }
        ]
    }
    response = client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    webhook.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert webhook.labels.count() == 1
    label = webhook.labels.first()
    assert label.key_id == key_id
    assert label.value_id == value_id

    response = client.patch(
        url,
        data=json.dumps({"labels": []}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    webhook.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert webhook.labels.count() == 0


@pytest.mark.django_db
def test_create_webhook_with_labels(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:webhooks-list")

    key_id = "testkey"
    value_id = "testvalue"
    data = {
        "name": "the_webhook",
        "url": TEST_URL,
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "http_method": "POST",
        "labels": [
            {
                "key": {"id": key_id, "name": "test", "prescribed": False},
                "value": {"id": value_id, "name": "testv", "prescribed": False},
            }
        ],
        "team": None,
    }

    response = client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == 201
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
        "integration_filter": [],
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
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
        "preset": None,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_update_webhook_labels_duplicate_key(
    webhook_internal_api_setup,
    make_user_auth_headers,
):
    user, token, webhook = webhook_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    key_id = "testkey"
    data = {
        "labels": [
            {"key": {"id": key_id, "name": "test"}, "value": {"id": "testvalue1", "name": "testv1"}},
            {"key": {"id": key_id, "name": "test"}, "value": {"id": "testvalue2", "name": "testv2"}},
        ]
    }
    response = client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    webhook.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert webhook.labels.count() == 0


@pytest.mark.django_db
def test_team_not_updated_if_not_in_data(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_custom_webhook,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    webhook = make_custom_webhook(
        name="some_webhook",
        url="https://github.com/",
        organization=organization,
        forward_all=False,
        team=team,
    )

    assert webhook.team == team

    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {"name": "renamed"}
    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["team"] == webhook.team.public_primary_key

    webhook.refresh_from_db()
    assert webhook.team == team
