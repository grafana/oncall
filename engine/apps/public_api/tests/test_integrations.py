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
                "inbound_email": None,
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
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
        "inbound_email": None,
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
def test_get_list_integrations_link_and_inbound_email(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_integration_heartbeat,
    settings,
):
    """
    Check that "link" and "inbound_email" fields are populated correctly for different integration types.
    """

    settings.BASE_URL = "https://test.com"
    settings.INBOUND_EMAIL_DOMAIN = "test.com"

    organization, user, token = make_organization_and_user_with_token()

    for integration in AlertReceiveChannel._config:
        make_alert_receive_channel(organization, integration=integration.slug, token="test123")

    client = APIClient()
    url = reverse("api-public:integrations-list")

    response = client.get(url, HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK

    for integration in response.json()["results"]:
        integration_type, integration_link, integration_inbound_email = (
            integration["type"],
            integration["link"],
            integration["inbound_email"],
        )

        if integration_type in [
            AlertReceiveChannel.INTEGRATION_MANUAL,
            AlertReceiveChannel.INTEGRATION_SLACK_CHANNEL,
            AlertReceiveChannel.INTEGRATION_MAINTENANCE,
        ]:
            assert integration_link is None
            assert integration_inbound_email is None
        elif integration_type == AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL:
            assert integration_link is None
            assert integration_inbound_email == "test123@test.com"
        else:
            assert integration_link == f"https://test.com/integrations/v1/{integration_type}/test123/"
            assert integration_inbound_email is None


@pytest.mark.django_db
def test_create_integration_default_route(
    make_organization_and_user_with_token,
    make_escalation_chain,
):
    organization, _, token = make_organization_and_user_with_token()
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_create = {
        "type": "grafana",
        "name": "grafana_created",
        "team_id": None,
        "default_route": {"escalation_chain_id": escalation_chain.public_primary_key},
    }
    url = reverse("api-public:integrations-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["default_route"]["escalation_chain_id"] == escalation_chain.public_primary_key


@pytest.mark.django_db
def test_update_integration_default_route(
    make_organization_and_user_with_token, make_escalation_chain, make_alert_receive_channel, make_channel_filter
):
    organization, _, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization)
    make_channel_filter(integration, is_default=True)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_update = {
        "default_route": {"escalation_chain_id": escalation_chain.public_primary_key},
    }

    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["default_route"]["escalation_chain_id"] == escalation_chain.public_primary_key


@pytest.mark.django_db
def test_create_integrations_direct_paging(
    make_organization_and_user_with_token, make_team, make_alert_receive_channel, make_user_auth_headers
):
    organization, _, token = make_organization_and_user_with_token()
    team = make_team(organization)

    client = APIClient()
    url = reverse("api-public:integrations-list")

    response_1 = client.post(url, data={"type": "direct_paging"}, format="json", HTTP_AUTHORIZATION=token)
    response_2 = client.post(url, data={"type": "direct_paging"}, format="json", HTTP_AUTHORIZATION=token)

    response_3 = client.post(
        url, data={"type": "direct_paging", "team_id": team.public_primary_key}, format="json", HTTP_AUTHORIZATION=token
    )
    response_4 = client.post(
        url, data={"type": "direct_paging", "team_id": team.public_primary_key}, format="json", HTTP_AUTHORIZATION=token
    )

    # Check direct paging integration for "No team" is created
    assert response_1.status_code == status.HTTP_201_CREATED
    # Check direct paging integration is not created, as it already exists for "No team"
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    # Check direct paging integration for team is created
    assert response_3.status_code == status.HTTP_201_CREATED
    # Check direct paging integration is not created, as it already exists for team
    assert response_4.status_code == status.HTTP_400_BAD_REQUEST
    assert response_4.data["detail"] == AlertReceiveChannel.DuplicateDirectPagingError.DETAIL


@pytest.mark.django_db
def test_update_integrations_direct_paging(
    make_organization_and_user_with_token, make_team, make_alert_receive_channel, make_user_auth_headers
):
    organization, _, token = make_organization_and_user_with_token()
    team = make_team(organization)

    integration = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=None
    )
    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=team)

    client = APIClient()
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])

    # Move direct paging integration from "No team" to team
    response = client.put(url, data={"team_id": team.public_primary_key}, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == AlertReceiveChannel.DuplicateDirectPagingError.DETAIL


@pytest.mark.django_db
def test_get_integration_type_legacy(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    am = make_alert_receive_channel(
        organization, verbal_name="AMV2", integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    )
    legacy_am = make_alert_receive_channel(
        organization, verbal_name="AMV2", integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER
    )

    client = APIClient()
    url = reverse("api-public:integrations-detail", args=[am.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["type"] == "alertmanager"

    url = reverse("api-public:integrations-detail", args=[legacy_am.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["type"] == "alertmanager"


@pytest.mark.django_db
def test_create_integration_type_legacy(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()

    client = APIClient()
    url = reverse("api-public:integrations-list")
    response = client.post(url, data={"type": "alertmanager"}, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["type"] == "alertmanager"

    response = client.post(url, data={"type": "legacy_alertmanager"}, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_integration_type_legacy(
    make_organization_and_user_with_token, make_alert_receive_channel, make_channel_filter, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_token()
    am = make_alert_receive_channel(
        organization, verbal_name="AMV2", integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    )
    legacy_am = make_alert_receive_channel(
        organization, verbal_name="AMV2", integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER
    )

    data_for_update = {"type": "alertmanager", "description_short": "Updated description"}

    client = APIClient()
    url = reverse("api-public:integrations-detail", args=[am.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["type"] == "alertmanager"
    assert response.data["description_short"] == "Updated description"

    url = reverse("api-public:integrations-detail", args=[legacy_am.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["description_short"] == "Updated description"
    assert response.data["type"] == "alertmanager"
