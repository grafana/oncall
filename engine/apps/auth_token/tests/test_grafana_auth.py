import typing
from unittest.mock import patch

import pytest
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory

from apps.auth_token.auth import (
    GRAFANA_SA_PREFIX,
    X_GRAFANA_INSTANCE_SLUG,
    X_GRAFANA_ORG_SLUG,
    GrafanaServiceAccountAuthentication,
)
from settings.base import CLOUD_LICENSE_NAME, OPEN_SOURCE_LICENSE_NAME, SELF_HOSTED_SETTINGS


def fake_authenticate_credentials(organization, token):
    pass


@pytest.mark.django_db
def test_grafana_authentication_oss_inputs(make_organization, settings):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    headers, token = check_common_inputs()
    organization = make_organization(
        stack_slug=SELF_HOSTED_SETTINGS["STACK_SLUG"], org_slug=SELF_HOSTED_SETTINGS["ORG_SLUG"]
    )
    request = APIRequestFactory().get("/", **headers)
    with patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate_credentials",
        wraps=fake_authenticate_credentials,
    ) as mock:
        GrafanaServiceAccountAuthentication().authenticate(request)
        mock.assert_called_once_with(organization, token)


@pytest.mark.django_db
def test_grafana_authentication_cloud_inputs(make_organization, settings):
    settings.LICENSE = CLOUD_LICENSE_NAME
    headers, token = check_common_inputs()

    test_org_slug = "test_org_123"
    test_stack_slug = "test_stack_123"
    headers[f"HTTP_{X_GRAFANA_ORG_SLUG}"] = test_org_slug
    headers[f"HTTP_{X_GRAFANA_INSTANCE_SLUG}"] = test_stack_slug
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    organization = make_organization(stack_slug=test_stack_slug, org_slug=test_org_slug)
    with patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate_credentials",
        wraps=fake_authenticate_credentials,
    ) as mock:
        GrafanaServiceAccountAuthentication().authenticate(request)
        mock.assert_called_once_with(organization, token)


def check_common_inputs() -> (dict[str, typing.Any], str):
    request = APIRequestFactory().get("/")
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    headers = {
        "HTTP_AUTHORIZATION": "xyz",
    }
    request = APIRequestFactory().get("/", **headers)
    result = GrafanaServiceAccountAuthentication().authenticate(request)
    assert result is None

    token = f"{GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
    }
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    return headers, token
