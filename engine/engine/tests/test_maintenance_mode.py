import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

MAINTENANCE_MODE_MSG = "asdfasdfasdf"


@pytest.mark.parametrize("setting_value", [MAINTENANCE_MODE_MSG, None])
@override_settings()
def test_get_maintenance_mode_status(setting_value):
    client = APIClient()

    with override_settings(CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE=setting_value):
        response = client.get("/api/internal/v1/maintenance-mode-status", format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["currently_undergoing_maintenance_message"] == setting_value
