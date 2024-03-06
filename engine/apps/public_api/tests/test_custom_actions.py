import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook


@pytest.mark.django_db
def test_get_custom_actions(make_organization_and_user_with_token, make_custom_webhook):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_webhook(organization=organization)

    url = reverse("api-public:actions-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": custom_action.public_primary_key,
                "name": custom_action.name,
                "team_id": None,
                "url": custom_action.url,
                "data": custom_action.data,
                "user": custom_action.user,
                "password": custom_action.password,
                "authorization_header": custom_action.authorization_header,
                "forward_whole_payload": custom_action.forward_all,
                "is_webhook_enabled": custom_action.is_webhook_enabled,
                "trigger_template": custom_action.trigger_template,
                "headers": custom_action.headers,
                "http_method": custom_action.http_method,
                "trigger_type": Webhook.PUBLIC_TRIGGER_TYPES_MAP[custom_action.trigger_type],
                "integration_filter": [i.public_primary_key for i in custom_action.filtered_integrations.all()] or None,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_custom_actions_filter_by_name(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_webhook(organization=organization)
    make_custom_webhook(organization=organization)
    url = reverse("api-public:actions-list")

    response = client.get(f"{url}?name={custom_action.name}", format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": custom_action.public_primary_key,
                "name": custom_action.name,
                "team_id": None,
                "url": custom_action.url,
                "data": custom_action.data,
                "user": custom_action.username,
                "password": custom_action.password,
                "authorization_header": custom_action.authorization_header,
                "forward_whole_payload": custom_action.forward_all,
                "is_webhook_enabled": custom_action.is_webhook_enabled,
                "trigger_template": custom_action.trigger_template,
                "headers": custom_action.headers,
                "http_method": custom_action.http_method,
                "trigger_type": Webhook.PUBLIC_TRIGGER_TYPES_MAP[custom_action.trigger_type],
                "integration_filter": [i.public_primary_key for i in custom_action.filtered_integrations.all()] or None,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_custom_actions_filter_by_name_empty_result(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    make_custom_webhook(organization=organization)

    url = reverse("api-public:actions-list")

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
def test_get_custom_action(
    make_organization_and_user_with_token,
    make_custom_webhook,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_webhook(organization=organization)

    url = reverse("api-public:actions-detail", kwargs={"pk": custom_action.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "id": custom_action.public_primary_key,
        "name": custom_action.name,
        "team_id": None,
        "url": custom_action.url,
        "data": custom_action.data,
        "user": custom_action.username,
        "password": custom_action.password,
        "authorization_header": custom_action.authorization_header,
        "forward_whole_payload": custom_action.forward_all,
        "is_webhook_enabled": custom_action.is_webhook_enabled,
        "trigger_template": custom_action.trigger_template,
        "headers": custom_action.headers,
        "http_method": custom_action.http_method,
        "trigger_type": Webhook.PUBLIC_TRIGGER_TYPES_MAP[custom_action.trigger_type],
        "integration_filter": [i.public_primary_key for i in custom_action.filtered_integrations.all()] or None,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload
