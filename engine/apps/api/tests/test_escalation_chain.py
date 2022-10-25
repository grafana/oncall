import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def escalation_chain_internal_api_setup(make_organization_and_user_with_plugin_token, make_escalation_chain):
    organization, user, token = make_organization_and_user_with_plugin_token()
    escalation_chain = make_escalation_chain(organization)
    return user, token, escalation_chain


@pytest.mark.django_db
def test_delete_escalation_chain(escalation_chain_internal_api_setup, make_user_auth_headers):
    user, token, escalation_chain = escalation_chain_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_chain-detail", kwargs={"pk": escalation_chain.public_primary_key})

    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_update_escalation_chain(escalation_chain_internal_api_setup, make_user_auth_headers):
    user, token, escalation_chain = escalation_chain_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_chain-detail", kwargs={"pk": escalation_chain.public_primary_key})
    data = {
        "name": "escalation_chain_updated",
        "organization": escalation_chain.organization.public_primary_key,
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_200_OK
