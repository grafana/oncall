import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_regex_is_required_for_route_regex_debugger(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_escalation_chain
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    client = APIClient()
    url = reverse("api-internal:route_regex_debugger")
    response = client.get(url, format="text/plain", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_invalid_regex_for_route_regex_debugger(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_escalation_chain
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    client = APIClient()
    url = reverse("api-internal:route_regex_debugger")
    response = client.get(f"{url}?regex=invalid_regex\\", format="text/plain", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
