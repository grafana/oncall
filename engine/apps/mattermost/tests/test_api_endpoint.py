import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.utils import live_settings

def _create_callback_request_body(token):
    return {"context": {"app": {"app_id": "oncall-app-id"}}, "state": {"auth_token": token}}


def _create_manifest_data(auth_token, base_url):
    return {
        "app_id": "Grafana-OnCall",
        "version": "1.0.0",
        "display_name": "Grafana OnCall",
        "description": "Grafana OnCall app for sending and receiving events from mattermost",
        "homepage_url": "https://grafana.com/docs/oncall/latest/",
        "requested_permissions": ["act_as_bot"],
        "requested_locations": ["/in_post", "/post_menu", "/command"],
        "on_install": {
            "path": "/mattermost/install",
            "expand": {"app": "summary", "acting_user": "summary"},
            "state": {"auth_token": auth_token},
        },
        "bindings": {"path": "/mattermost/bindings", "state": {"auth_token": auth_token}},
        "http": {"root_url": base_url},
    }


@pytest.mark.django_db
def test_get_manifest_data_success(
    settings, make_organization_and_user, make_mattermost_app_verification_token_for_user
):
    organization, user = make_organization_and_user()
    _, token = make_mattermost_app_verification_token_for_user(user, organization)
    url = reverse("mattermost:manifest")
    live_settings.MATTERMOST_WEBHOOK_HOST = "https://oncallengine.com"

    client = APIClient()
    response = client.get(url + f"?auth_token={token}")
    assert response.status_code == status.HTTP_200_OK

    expected_manifest_data = _create_manifest_data(token, live_settings.MATTERMOST_WEBHOOK_HOST)
    assert response.json() == expected_manifest_data


@pytest.mark.django_db
def test_get_manifest_data_forbidden(make_organization_and_user, make_mattermost_app_verification_token_for_user):
    organization, user = make_organization_and_user()
    _, _ = make_mattermost_app_verification_token_for_user(user, organization)
    url = reverse("mattermost:manifest")
    client = APIClient()
    response = client.get(url + "?auth_token=wrongtoken")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_install_callback_success(make_organization_and_user, make_mattermost_app_verification_token_for_user):
    organization, user = make_organization_and_user()
    _, token = make_mattermost_app_verification_token_for_user(user, organization)
    url = reverse("mattermost:install")
    client = APIClient()
    data = _create_callback_request_body(token)
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["type"] == "ok"


@pytest.mark.django_db
def test_bindings_callback_success(make_organization_and_user, make_mattermost_app_verification_token_for_user):
    organization, user = make_organization_and_user()
    _, token = make_mattermost_app_verification_token_for_user(user, organization)
    url = reverse("mattermost:bindings")
    client = APIClient()
    data = _create_callback_request_body(token)
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["type"] == "ok"


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["install", "bindings"])
def test_install_callback_forbiden(make_organization_and_user, make_mattermost_app_verification_token_for_user, path):
    organization, user = make_organization_and_user()
    _, _ = make_mattermost_app_verification_token_for_user(user, organization)
    url = reverse(f"mattermost:{path}")
    client = APIClient()
    data = _create_callback_request_body("wrongtoken")
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
