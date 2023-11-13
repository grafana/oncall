from unittest.mock import patch

import pytest
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.auth_token.constants import SLACK_AUTH_TOKEN_NAME


@pytest.mark.django_db
@pytest.mark.parametrize(
    "backend_name,expected_url",
    (
        ("slack-login", "/a/grafana-oncall-app/users/me"),
        ("slack-install-free", "/a/grafana-oncall-app/chat-ops"),
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
        reverse("api-internal:complete-slack-auth", kwargs={"backend": backend_name})
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
        reverse("api-internal:complete-slack-auth", kwargs={"backend": "slack-login"})
        + f"?{SLACK_AUTH_TOKEN_NAME}={slack_token}"
    )

    def _custom_do_complete(backend, *args, **kwargs):
        backend.strategy.session[REDIRECT_FIELD_NAME] = "some-url"
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    with patch("apps.api.views.auth.do_complete", side_effect=_custom_do_complete):
        response = client.get(url)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "some-url"
