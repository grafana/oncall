import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_get_terraform_file(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_escalation_chain
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    client = APIClient()
    url = reverse("api-internal:terraform_file")
    response = client.get(url, format="text/plain", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_terraform_imports(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    _, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:terraform_imports")
    response = client.get(url, format="text/plain", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
