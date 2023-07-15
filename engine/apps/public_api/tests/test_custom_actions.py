import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_get_custom_actions(
    make_organization_and_user_with_token,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_action(organization=organization)

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
                "url": custom_action.webhook,
                "data": custom_action.data,
                "user": custom_action.user,
                "password": custom_action.password,
                "authorization_header": custom_action.authorization_header,
                "forward_whole_payload": custom_action.forward_whole_payload,
            }
        ],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_custom_actions_filter_by_name(
    make_organization_and_user_with_token,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_action(organization=organization)
    make_custom_action(organization=organization)
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
                "url": custom_action.webhook,
                "data": custom_action.data,
                "user": custom_action.user,
                "password": custom_action.password,
                "authorization_header": custom_action.authorization_header,
                "forward_whole_payload": custom_action.forward_whole_payload,
            }
        ],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_custom_actions_filter_by_name_empty_result(
    make_organization_and_user_with_token,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    make_custom_action(organization=organization)

    url = reverse("api-public:actions-list")

    response = client.get(f"{url}?name=NonExistentName", format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {"count": 0, "next": None, "previous": None, "results": []}

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload


@pytest.mark.django_db
def test_get_custom_action(
    make_organization_and_user_with_token,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    custom_action = make_custom_action(organization=organization)

    url = reverse("api-public:actions-detail", kwargs={"pk": custom_action.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "id": custom_action.public_primary_key,
        "name": custom_action.name,
        "team_id": None,
        "url": custom_action.webhook,
        "data": custom_action.data,
        "user": custom_action.user,
        "password": custom_action.password,
        "authorization_header": custom_action.authorization_header,
        "forward_whole_payload": custom_action.forward_whole_payload,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload
