import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_user_settings_get(make_organization_and_user_with_mobile_app_auth_token):
    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

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
        "important_notification_sound_name": "default_sound_important",
        "important_notification_volume_type": "constant",
        "important_notification_volume": 0.8,
        "important_notification_override_dnd": True,
        "info_notifications_enabled": True,
        "going_oncall_notification_timing": 1,
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
        "important_notification_sound_name": "test_important",
        "important_notification_volume_type": "intensifying",
        "important_notification_volume": 1,
        "important_notification_override_dnd": False,
        "info_notifications_enabled": False,
        "going_oncall_notification_timing": 3,
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    # Check the values are updated correctly
    assert response.json() == data
