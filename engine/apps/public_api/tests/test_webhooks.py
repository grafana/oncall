import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook


def _get_expected_result(webhook):
    return {
        "id": webhook.public_primary_key,
        "name": webhook.name,
        "team": webhook.team,
        "url": webhook.url,
        "data": webhook.data,
        "username": webhook.username,
        "password": webhook.password,
        "authorization_header": webhook.authorization_header,
        "forward_all": webhook.forward_all,
        "is_webhook_enabled": webhook.is_webhook_enabled,
        "trigger_template": webhook.trigger_template,
        "headers": webhook.headers,
        "http_method": webhook.http_method,
        "trigger_type": Webhook.PUBLIC_TRIGGER_TYPES_MAP[webhook.trigger_type],
        "integration_filter": webhook.integration_filter,
    }


@pytest.mark.django_db
def test_get_webhooks(make_organization_and_user_with_token, make_custom_webhook):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)

    url = reverse("api-public:webhooks-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [_get_expected_result(webhook)],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_webhooks_filter_by_name(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)
    make_custom_webhook(organization=organization)
    url = reverse("api-public:webhooks-list")

    response = client.get(f"{url}?name={webhook.name}", format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [_get_expected_result(webhook)],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_webhooks_filter_by_name_empty_result(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    make_custom_webhook(organization=organization)

    url = reverse("api-public:webhooks-list")

    response = client.get(f"{url}?name=NonExistentName", format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_webhook(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)

    url = reverse("api-public:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = _get_expected_result(webhook)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_create_webhook(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:webhooks-list")

    data = {}

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data["name"] = "Test outgoing webhook"

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data["url"] = "https://example.com"

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data["trigger_type"] = "escalation"

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data["http_method"] = "POST"

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_201_CREATED
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])

    expected_result = _get_expected_result(webhook)

    assert response.data == expected_result


@pytest.mark.django_db
def test_create_webhook_nested_data(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse("api-public:webhooks-list")

    data = {
        "name": "Test outgoing webhook with nested data",
        "url": "https://example.com",
        "data": '{"nested_item": "{{ alert_payload.foo.bar | to_json }}"}',
        "http_method": "POST",
        "trigger_type": "acknowledge",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data["data"] = '{"nested_item": "{{ alert_payload.foo.bar | tojson() }}"}'

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])

    expected_result = _get_expected_result(webhook)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_result


@pytest.mark.django_db
def test_update_webhook(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)
    url = reverse("api-public:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {
        "name": "RENAMED",
    }
    assert webhook.name != data["name"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_result = _get_expected_result(webhook)
    expected_result["name"] = data["name"]

    assert response.status_code == status.HTTP_200_OK
    webhook.refresh_from_db()
    assert webhook.name == expected_result["name"]
    assert response.data == expected_result


@pytest.mark.django_db
def test_delete_webhook(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)
    url = reverse("api-public:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    assert webhook.deleted_at is None

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    webhook.refresh_from_db()
    assert webhook.deleted_at is not None

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "Not found."


@pytest.mark.django_db
def test_get_webhook_responses(
    make_organization_and_user_with_token,
    make_custom_webhook,
    make_webhook_response,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    webhook = make_custom_webhook(organization=organization)
    webhook.refresh_from_db()

    response_count = 20
    for i in range(0, response_count):
        make_webhook_response(
            webhook=webhook,
            trigger_type=webhook.trigger_type,
            status_code=200,
            content=json.dumps({"id": "third-party-id"}),
            event_data=json.dumps({"test": "abc"}),
        )

    url = reverse("api-public:webhooks-responses", kwargs={"pk": webhook.public_primary_key})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    webhook_response = response.data["results"][0]
    assert webhook_response["status_code"] == 200
    assert webhook_response["content"] == '{"id": "third-party-id"}'
    assert webhook_response["event_data"] == '{"test": "abc"}'
    assert response.data["count"] == 20
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_webhook_validate_integration_filters(
    make_organization_and_user_with_token,
    make_custom_webhook,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    webhook = make_custom_webhook(organization=organization)
    url = reverse("api-public:webhooks-detail", kwargs={"pk": webhook.public_primary_key})
    data = {"integration_filter": alert_receive_channel.public_primary_key}

    client = APIClient()
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == 400

    data["integration_filter"] = ["abc"]
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == 400

    data["integration_filter"] = [alert_receive_channel.public_primary_key, alert_receive_channel.public_primary_key]
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == 400

    data["integration_filter"] = [alert_receive_channel.public_primary_key]
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    webhook.refresh_from_db()
    assert response.status_code == 200
    assert response.data["integration_filter"] == data["integration_filter"]
    assert webhook.integration_filter == data["integration_filter"]

    data["integration_filter"] = []
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    webhook.refresh_from_db()
    assert response.status_code == 200
    assert response.data["integration_filter"] == data["integration_filter"]
    assert webhook.integration_filter == data["integration_filter"]

    data["integration_filter"] = None
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    webhook.refresh_from_db()
    assert response.status_code == 200
    assert response.data["integration_filter"] == data["integration_filter"]
    assert webhook.integration_filter == data["integration_filter"]
