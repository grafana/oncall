import httpretty
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api import permissions
from apps.auth_token.tests.helpers import setup_service_account_api_mocks


@pytest.mark.django_db
def test_get_escalation_chains(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain = organization.escalation_chains.create(name="test")

    client = APIClient()

    url = reverse("api-public:escalation_chains-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": escalation_chain.public_primary_key,
                "team_id": None,
                "name": "test",
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_data


@pytest.mark.django_db
def test_create_escalation_chain(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()

    data = {"name": "test", "team_id": None}

    client = APIClient()
    url = reverse("api-public:escalation_chains-list")
    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    escalation_chain = organization.escalation_chains.get(name="test")
    expected_data = {
        "id": escalation_chain.public_primary_key,
        "team_id": None,
        "name": "test",
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == expected_data


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_create_escalation_chain_via_service_account(
    make_organization,
    make_service_account_for_organization,
    make_token_for_service_account,
    make_team,
):
    organization = make_organization(grafana_url="http://grafana.test")
    team = make_team(organization=organization)
    service_account = make_service_account_for_organization(organization)
    token_string = "glsa_token"
    make_token_for_service_account(service_account, token_string)

    perms = {
        permissions.RBACPermission.Permissions.ESCALATION_CHAINS_WRITE.value: ["*"],
    }
    setup_service_account_api_mocks(organization.grafana_url, perms)

    client = APIClient()
    url = reverse("api-public:escalation_chains-list")
    data = {"name": "test", "team_id": team.public_primary_key}
    response = client.post(
        url,
        data=data,
        format="json",
        HTTP_AUTHORIZATION=f"{token_string}",
        HTTP_X_GRAFANA_URL=organization.grafana_url,
    )
    assert response.status_code == status.HTTP_201_CREATED
    escalation_chain = organization.escalation_chains.get(name="test")
    assert escalation_chain.team == team


@pytest.mark.django_db
def test_change_name(make_organization_and_user_with_token):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain = organization.escalation_chains.create(name="test")

    data = {
        "id": escalation_chain.public_primary_key,
        "name": "changed",
    }

    client = APIClient()
    url = reverse("api-public:escalation_chains-detail", kwargs={"pk": escalation_chain.public_primary_key})
    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    expected_data = {
        "id": escalation_chain.public_primary_key,
        "team_id": None,
        "name": "changed",
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_data
