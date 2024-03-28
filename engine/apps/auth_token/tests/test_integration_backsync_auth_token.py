import pytest
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.auth_token.auth import IntegrationBacksyncAuthentication, ServerUser


@pytest.mark.django_db
def test_integration_token_auth(make_organization_and_user, make_alert_receive_channel, make_token_for_integration):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    integration_token, token_string = make_token_for_integration(alert_receive_channel, organization)

    headers = {"HTTP_AUTHORIZATION": token_string}
    request = APIRequestFactory().get("/", **headers)

    assert IntegrationBacksyncAuthentication().authenticate(request) == (ServerUser(), integration_token)


@pytest.mark.django_db
def test_integration_token_wrong_token(make_organization_and_user, make_alert_receive_channel):
    organization, _ = make_organization_and_user()
    token_string = "somerandomteasttokenstring"
    headers = {"HTTP_AUTHORIZATION": token_string}
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(AuthenticationFailed):
        IntegrationBacksyncAuthentication().authenticate(request)


@pytest.mark.django_db
def test_integration_token_revoked(make_organization_and_user, make_alert_receive_channel, make_token_for_integration):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    integration_token, token_string = make_token_for_integration(alert_receive_channel, organization)
    # revoke token
    integration_token.delete()
    headers = {"HTTP_AUTHORIZATION": token_string}
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(AuthenticationFailed):
        IntegrationBacksyncAuthentication().authenticate(request)
