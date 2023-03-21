import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_user_settings_get(make_organization_and_user_with_mobile_app_auth_token):
    organization, user, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:user_settings")

    response = client.get(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    # Check the default values are correct
    assert response.json() == {
        "default_notification_sound_name": "default_sound",
        "default_notification_volume_type": "constant",
        "default_notification_volume": 0.8,
        "default_notification_volume_override": False,
        "critical_notification_sound_name": "default_sound_important",
        "critical_notification_volume_type": "constant",
        "critical_notification_volume": 0.8,
        "critical_notification_override_dnd": True,
    }


@pytest.mark.django_db
def test_user_settings_put(make_organization_and_user_with_mobile_app_auth_token):
    organization, user, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:user_settings")
    data = {
        "default_notification_sound_name": "test_default",
        "default_notification_volume_type": "intensifying",
        "default_notification_volume": 1,
        "default_notification_volume_override": True,
        "critical_notification_sound_name": "test_critical",
        "critical_notification_volume_type": "intensifying",
        "critical_notification_volume": 1,
        "critical_notification_override_dnd": False,
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    # Check the values are updated correctly
    assert response.json() == data
