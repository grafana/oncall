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
        "info_notification_sound_name": "default_sound",
        "info_notification_volume_type": "constant",
        "info_notification_volume": 0.8,
        "info_notification_volume_override": False,
        "important_notification_sound_name": "default_sound_important",
        "important_notification_volume_type": "constant",
        "important_notification_volume": 0.8,
        "important_notification_volume_override": True,
        "important_notification_override_dnd": True,
        "info_notifications_enabled": False,
        "going_oncall_notification_timing": 43200,
        "locale": None,
        "time_zone": "UTC",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "going_oncall_notification_timing,expected_status_code",
    [
        (43200, status.HTTP_200_OK),
        (86400, status.HTTP_200_OK),
        (604800, status.HTTP_200_OK),
        (500, status.HTTP_400_BAD_REQUEST),
    ],
)
def test_user_settings_put(
    make_organization_and_user_with_mobile_app_auth_token, going_oncall_notification_timing, expected_status_code
):
    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:user_settings")
    data = {
        "default_notification_sound_name": "test_default",
        "default_notification_volume_type": "intensifying",
        "default_notification_volume": 1,
        "default_notification_volume_override": True,
        "info_notification_sound_name": "default_sound",
        "info_notification_volume_type": "constant",
        "info_notification_volume": 0.8,
        "info_notification_volume_override": False,
        "important_notification_sound_name": "test_important",
        "important_notification_volume_type": "intensifying",
        "important_notification_volume": 1,
        "important_notification_volume_override": False,
        "important_notification_override_dnd": False,
        "info_notifications_enabled": True,
        "going_oncall_notification_timing": going_oncall_notification_timing,
        "locale": "ca_FR",
        "time_zone": "Europe/Paris",
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == expected_status_code

    if expected_status_code == status.HTTP_200_OK:
        # Check the values are updated correctly
        assert response.json() == data


@pytest.mark.django_db
def test_user_settings_patch(make_organization_and_user_with_mobile_app_auth_token):
    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    original_default_notification_sound_name = "test_default"
    patch_default_notification_sound_name = "test_default_patched"

    client = APIClient()
    url = reverse("mobile_app:user_settings")
    data = {
        "default_notification_sound_name": original_default_notification_sound_name,
        "default_notification_volume_type": "intensifying",
        "default_notification_volume": 1,
        "default_notification_volume_override": True,
        "info_notification_sound_name": "default_sound",
        "info_notification_volume_type": "constant",
        "info_notification_volume": 0.8,
        "info_notification_volume_override": False,
        "important_notification_sound_name": "test_important",
        "important_notification_volume_type": "intensifying",
        "important_notification_volume": 1,
        "important_notification_volume_override": False,
        "important_notification_override_dnd": False,
        "info_notifications_enabled": True,
        "time_zone": "Europe/Luxembourg",
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=auth_token)
    original_settings = response.json()

    assert response.status_code == status.HTTP_200_OK

    patch_data = {"default_notification_sound_name": patch_default_notification_sound_name}
    response = client.patch(url, data=patch_data, format="json", HTTP_AUTHORIZATION=auth_token)

    assert response.status_code == status.HTTP_200_OK
    # all original settings should stay the same, only data set in PATCH call should get updated
    assert response.json() == {**original_settings, **patch_data}


@pytest.mark.django_db
def test_user_settings_time_zone_must_be_valid(make_organization_and_user_with_mobile_app_auth_token):
    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    valid_timezone = {"time_zone": "Europe/Luxembourg"}
    invalid_timezone = {"time_zone": "asdflkjasdlkj"}
    null_timezone = {"time_zone": None}

    client = APIClient()
    url = reverse("mobile_app:user_settings")

    response = client.put(url, data=valid_timezone, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    response = client.put(url, data=invalid_timezone, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.put(url, data=null_timezone, format="json", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
