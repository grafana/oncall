import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.base.tests.messaging_backend import TestOnlyBackend

TEST_MESSAGING_BACKEND_FIELD = TestOnlyBackend.backend_id.lower()


@pytest.mark.django_db
def test_get_list_integrations(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_integration_heartbeat,
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana", description_short="Some description")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    expected_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": integration.public_primary_key,
                "team_id": None,
                "name": "grafana",
                "description_short": "Some description",
                "link": integration.integration_url,
                "type": "grafana",
                "default_route": {
                    "escalation_chain_id": None,
                    "id": default_channel_filter.public_primary_key,
                    "slack": {"channel_id": None, "enabled": True},
                    "telegram": {"id": None, "enabled": False},
                    TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
                },
                "heartbeat": {
                    "link": f"{integration.integration_url}heartbeat/",
                },
                "templates": {
                    "grouping_key": None,
                    "resolve_signal": None,
                    "acknowledge_signal": None,
                    "source_link": None,
                    "slack": {"title": None, "message": None, "image_url": None},
                    "web": {"title": None, "message": None, "image_url": None},
                    "sms": {
                        "title": None,
                    },
                    "phone_call": {
                        "title": None,
                    },
                    "telegram": {
                        "title": None,
                        "message": None,
                        "image_url": None,
                    },
                    TEST_MESSAGING_BACKEND_FIELD: {
                        "title": None,
                        "message": None,
                        "image_url": None,
                    },
                },
                "maintenance_mode": None,
                "maintenance_started_at": None,
                "maintenance_end_at": None,
            }
        ],
    }
    url = reverse("api-public:integrations-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_integration(
    make_organization_and_user_with_token,
    make_escalation_chain,
):
    organization, _, token = make_organization_and_user_with_token()
    make_escalation_chain(organization)

    client = APIClient()
    data_for_create = {
        "type": "grafana",
        "name": "grafana_created",
        "team_id": None,
    }
    url = reverse("api-public:integrations-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_integrations_with_none_templates(
    make_organization_and_user_with_token,
    make_escalation_chain,
):
    organization, _, token = make_organization_and_user_with_token()
    make_escalation_chain(organization)

    client = APIClient()
    data_for_create = {
        "type": "grafana",
        "team_id": None,
        "name": "grafana_created",
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "slack": None,
            "web": None,
            "sms": None,
            "phone_call": None,
            "telegram": None,
        },
    }

    url = reverse("api-public:integrations-list")

    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_integration_with_invalid_type(
    make_organization_and_user_with_token,
):
    _, _, token = make_organization_and_user_with_token()

    client = APIClient()
    data_for_create = {
        "type": "this_is_invalid_integration_type",
        "name": "grafana_created",
        "team_id": None,
    }
    url = reverse("api-public:integrations-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_integration_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"grouping_key": "ip_addr", "slack": {"title": "Incident"}}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": "ip_addr",
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": "Incident", "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_update_integration_template_messaging_backend(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"grouping_key": "ip_addr", TEST_MESSAGING_BACKEND_FIELD: {"title": "Incident"}}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": "ip_addr",
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": "Incident",
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_update_invalid_integration_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"slack": {"title": "{%  invalid jinja template }}"}}}
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_resolve_signal_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"resolve_signal": "resig"}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": "resig",
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_update_invalid_resolve_signal_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"resolve_signal": "{%  invalid jinja template }}"}}
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_empty_grouping_key_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"grouping_key": {}}}
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_invalid_flat_web_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"web": "invalid_web_template"}}
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_sms_template_with_empty_dict(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"sms": {}}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_update_integration_name(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"name": "grafana_updated"}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana_updated",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_update_integration_name_and_description_short(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana", description_short="Some description")
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"name": "grafana_updated"}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana_updated",
        "description_short": "Some description",
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_set_default_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, verbal_name="grafana")
    integration.slack_title_template = "updated_template"
    integration.grouping_id_template = "updated_template"
    integration.save()
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"grouping_key": None, "slack": {"title": None}}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": None,
                "image_url": None,
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_set_default_messaging_backend_template(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(
        organization,
        verbal_name="grafana",
        messaging_backends_templates={
            "TESTONLY": {"title": "the-title", "message": "the-message", "image_url": "the-image-url"}
        },
    )
    default_channel_filter = make_channel_filter(integration, is_default=True)
    make_integration_heartbeat(integration)

    client = APIClient()
    data_for_update = {"templates": {"testonly": {"title": None}}}
    expected_response = {
        "id": integration.public_primary_key,
        "team_id": None,
        "name": "grafana",
        "description_short": None,
        "link": integration.integration_url,
        "type": "grafana",
        "default_route": {
            "escalation_chain_id": None,
            "id": default_channel_filter.public_primary_key,
            "slack": {"channel_id": None, "enabled": True},
            "telegram": {"id": None, "enabled": False},
            TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
        },
        "heartbeat": {
            "link": f"{integration.integration_url}heartbeat/",
        },
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "acknowledge_signal": None,
            "source_link": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "sms": {
                "title": None,
            },
            "phone_call": {
                "title": None,
            },
            "telegram": {
                "title": None,
                "message": None,
                "image_url": None,
            },
            TEST_MESSAGING_BACKEND_FIELD: {
                "title": None,
                "message": "the-message",
                "image_url": "the-image-url",
            },
        },
        "maintenance_mode": None,
        "maintenance_started_at": None,
        "maintenance_end_at": None,
    }
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response


@pytest.mark.django_db
def test_get_list_integrations_direct_paging_hidden(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_integration_heartbeat,
):
    organization, user, token = make_organization_and_user_with_token()
    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)

    client = APIClient()
    url = reverse("api-public:integrations-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    # Check no direct paging integrations in the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []
