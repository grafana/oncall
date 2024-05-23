from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.chatops_proxy.events import ChatopsEventsHandler

installation_event = {
    "event_type": "integration_installed",
    "data": {
        "provider_type": "slack",
        "stack_id": "stack_id",
        "grafana_user_id": "grafana_user_id",
        "payload": {},
    },
}

unknown_event = {
    "event_type": "unknown_event",
    "data": {
        "provider_type": "slack",
        "stack_id": "stack_id",
        "grafana_user_id": "grafana_user_id",
        "payload": {},
    },
}

invalid_schema_event = {
    "a": "b",
    "c": "d",
}


@patch.object(ChatopsEventsHandler, "_exec", return_value=None)
@pytest.mark.parametrize(
    "payload,expected_status",
    [
        (installation_event, status.HTTP_200_OK),
        (unknown_event, status.HTTP_400_BAD_REQUEST),
        (invalid_schema_event, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_event_handler(payload, expected_status, mock_exec):
    client = APIClient()

    url = reverse("chatops-proxy:events")
    response = client.post(url, format="json", data=payload)
    assert response.status_code == expected_status
