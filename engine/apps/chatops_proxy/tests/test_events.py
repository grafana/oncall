from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.chatops_proxy.events import ChatopsEventsHandler
from apps.chatops_proxy.events.handlers import SlackInstallationHandler

installation_event = {
    "event_type": "integration_installed",
    "data": {
        "provider_type": "slack",
        "stack_id": "stack_id",
        "grafana_user_id": "grafana_user_id",
        "payload": {
            # It's not actual payload we are getting from slack, just a placeholder
            "slack_id"
            "some_slack_id"
        },
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
@override_settings(UNIFIED_SLACK_APP_ENABLED=True)
def test_root_event_handler(mock_exec, payload, expected_status):
    client = APIClient()

    url = reverse("chatops_proxy:events")
    response = client.post(url, format="json", data=payload)
    assert response.status_code == expected_status


@patch("apps.chatops_proxy.events.handlers.install_slack_integration", return_value=None)
@pytest.mark.django_db
@override_settings(UNIFIED_SLACK_APP_ENABLED=True)
def test_slack_installation_handler(mock_install_slack_integration, make_organization_and_user):
    organization, user = make_organization_and_user()

    installation_event["data"].update({"stack_id": organization.stack_id, "grafana_user_id": user.user_id})

    h = SlackInstallationHandler()

    assert h.match(unknown_event) is False
    assert h.match(invalid_schema_event) is False

    assert h.match(installation_event) is True
    h.handle(installation_event["data"])
    assert mock_install_slack_integration.call_args.args == (organization, user, installation_event["data"]["payload"])
