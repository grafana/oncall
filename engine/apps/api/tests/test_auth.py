from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.auth_token.constants import SLACK_AUTH_TOKEN_NAME
from apps.social_auth.backends import SLACK_INSTALLATION_BACKEND
from common.constants.slack_auth import SLACK_OAUTH_ACCESS_RESPONSE


@pytest.mark.django_db
@pytest.mark.parametrize(
    "backend_name,expected_url",
    (
        ("slack-login", "/a/grafana-oncall-app/users/me"),
        (SLACK_INSTALLATION_BACKEND, "/a/grafana-oncall-app/chat-ops"),
    ),
)
def test_complete_slack_auth_redirect_ok(
    make_organization,
    make_user_for_organization,
    make_slack_token_for_user,
    backend_name,
    expected_url,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, slack_token = make_slack_token_for_user(admin)

    client = APIClient()
    url = (
        reverse("api-internal:complete-social-auth", kwargs={"backend": backend_name})
        + f"?{SLACK_AUTH_TOKEN_NAME}={slack_token}"
    )

    with patch("apps.api.views.auth.do_complete") as mock_do_complete:
        mock_do_complete.return_value = None
        response = client.get(url)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == expected_url


@pytest.mark.django_db
def test_complete_slack_auth_redirect_error(
    make_organization,
    make_user_for_organization,
    make_slack_token_for_user,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, slack_token = make_slack_token_for_user(admin)

    client = APIClient()
    url = (
        reverse("api-internal:complete-social-auth", kwargs={"backend": "slack-login"})
        + f"?{SLACK_AUTH_TOKEN_NAME}={slack_token}"
    )

    def _custom_do_complete(backend, *args, **kwargs):
        backend.strategy.session[REDIRECT_FIELD_NAME] = "some-url"
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    with patch("apps.api.views.auth.do_complete", side_effect=_custom_do_complete):
        response = client.get(url)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "some-url"


@override_settings(UNIFIED_SLACK_APP_ENABLED=False)
@pytest.mark.django_db
def test_start_slack_ok(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """
    Covers the case when user starts Slack integration installation via Grafana OnCall
    """
    _, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:social-auth", kwargs={"backend": SLACK_INSTALLATION_BACKEND})

    mock_do_auth_return = Mock()
    mock_do_auth_return.url = "https://slack_oauth_redirect.com"
    with patch("apps.api.views.auth.do_auth", return_value=mock_do_auth_return) as mock_do_auth:
        response = client.get(url, **make_user_auth_headers(user, token))
        assert mock_do_auth.called
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "https://slack_oauth_redirect.com"


@override_settings(UNIFIED_SLACK_APP_ENABLED=True)
@pytest.mark.django_db
def test_start_unified_slack_ok(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """
    Covers the case when user starts Unified Slack integration installation
    """
    _, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:social-auth", kwargs={"backend": SLACK_INSTALLATION_BACKEND})

    with patch(
        "apps.api.views.auth.get_installation_link_from_chatops_proxy", return_value="https://slack_oauth_redirect.com"
    ):
        response = client.get(url, **make_user_auth_headers(user, token))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "https://slack_oauth_redirect.com"


@override_settings(UNIFIED_SLACK_APP_ENABLED=True)
@patch("apps.api.views.auth.get_installation_link_from_chatops_proxy", return_value=None)
@patch("apps.api.views.auth.get_slack_oauth_response_from_chatops_proxy", return_value=SLACK_OAUTH_ACCESS_RESPONSE)
@patch("apps.api.views.auth.install_slack_integration", return_value=None)
@pytest.mark.django_db
def test_start_slack_ok_via_chatops_proxy_when_already_installed(
    mock_install_slack_integration,
    mock_get_slack_oauth_response_from_chatops_proxy,
    mock_get_installation_link_from_chatops_proxy,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """
    Covers the case when user starts Unified Slack integration installation, but it's already installed.
    It might happen if integration was installed from Incident side, but OnCall missed the corresponding event
    """
    org, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:social-auth", kwargs={"backend": SLACK_INSTALLATION_BACKEND})

    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED
    assert mock_install_slack_integration.call_args.args == (org, user, SLACK_OAUTH_ACCESS_RESPONSE)


@pytest.mark.django_db
@patch("apps.social_auth.backends.GoogleOAuth2.get_redirect_uri")
@patch("apps.social_auth.backends.GoogleOAuth2Token.create_auth_token", return_value=("something", "token_string"))
@override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE=["https://www.googleapis.com/auth/calendar.events.readonly"])
@override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="ouath2_key")
def test_google_start_auth_redirect_ok(
    _mock_create_google_oauth2_auth_token,
    mock_google_oauth2_backend_get_redirect_uri,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    redirect_uri = "http://testserver"
    mock_google_oauth2_backend_get_redirect_uri.return_value = redirect_uri

    _, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:social-auth", kwargs={"backend": "google-oauth2"})
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == (
        "https://accounts.google.com/o/oauth2/auth?client_id=ouath2_key"
        f"&redirect_uri={redirect_uri}&response_type=code"
        "&state=token_string&scope=https://www.googleapis.com/auth/calendar.events.readonly+openid+email+profile"
        "&access_type=offline&approval_prompt=auto"
    )


@pytest.mark.django_db
@patch("apps.api.views.auth.do_complete", return_value=None)
def test_google_complete_auth_redirect_ok(
    _mock_do_complete,
    make_organization,
    make_user_for_organization,
    make_google_oauth2_token_for_user,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, google_oauth2_token = make_google_oauth2_token_for_user(admin)

    client = APIClient()
    url = (
        reverse("api-internal:complete-social-auth", kwargs={"backend": "google-oauth2"})
        + f"?state={google_oauth2_token}"
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "/a/grafana-oncall-app/users/me"
