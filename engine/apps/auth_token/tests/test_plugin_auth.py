import json
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.auth_token.auth import PluginAuthentication

INSTANCE_CONTEXT = '{"stack_id": 42, "org_id": 24, "grafana_token": "abc"}'


@pytest.mark.django_db
def test_plugin_authentication_self_hosted_success(make_organization, make_user, make_token_for_organization):
    organization = make_organization(stack_id=42, org_id=24)
    user = make_user(organization=organization, user_id=12)
    token, token_string = make_token_for_organization(organization)

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X-Instance-Context": INSTANCE_CONTEXT,
        "HTTP_X-Grafana-Context": '{"UserId": 12}',
    }
    request = APIRequestFactory().get("/", **headers)

    assert PluginAuthentication().authenticate(request) == (user, token)


@pytest.mark.django_db
def test_plugin_authentication_gcom_success(make_organization, make_user, make_token_for_organization):
    # Setting gcom_token_org_last_time_synced to now, so it doesn't try to sync with gcom
    organization = make_organization(
        stack_id=42, org_id=24, gcom_token="123", api_token="abc", gcom_token_org_last_time_synced=timezone.now()
    )
    user = make_user(organization=organization, user_id=12)

    headers = {
        "HTTP_AUTHORIZATION": "gcom:123",
        "HTTP_X-Instance-Context": INSTANCE_CONTEXT,
        "HTTP_X-Grafana-Context": '{"UserId": 12}',
    }
    request = APIRequestFactory().get("/", **headers)

    ret_user, ret_token = PluginAuthentication().authenticate(request)
    assert ret_user == user
    assert ret_token.organization == organization


@pytest.mark.django_db
@pytest.mark.parametrize("grafana_context", [None, "", "non-json", '"string"', "{}", '{"UserId": 1}'])
def test_plugin_authentication_fail_grafana_context(
    make_organization, make_user, make_token_for_organization, grafana_context
):
    organization = make_organization(stack_id=42, org_id=24)
    token, token_string = make_token_for_organization(organization)

    headers = {"HTTP_AUTHORIZATION": token_string, "HTTP_X-Instance-Context": INSTANCE_CONTEXT}
    if grafana_context is not None:
        headers["HTTP_X-Grafana-Context"] = grafana_context

    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(AuthenticationFailed):
        PluginAuthentication().authenticate(request)


@pytest.mark.django_db
@pytest.mark.parametrize("authorization", [None, "", "123", "gcom:123"])
@pytest.mark.parametrize(
    "instance_context", [None, "", "non-json", '"string"', "{}", '{"stack_id": 1, "org_id": 1, "grafana_token": "abc"}']
)
def test_plugin_authentication_fail(authorization, instance_context):
    headers = {}

    if authorization is not None:
        headers["HTTP_AUTHORIZATION"] = authorization

    if instance_context is not None:
        headers["HTTP_X-Instance-Context"] = instance_context

    request = APIRequestFactory().get("/", **headers)

    class MockCheckTokenResponse:
        organization = None

    with patch("apps.auth_token.auth.check_token", return_value=MockCheckTokenResponse):
        with pytest.raises(AuthenticationFailed):
            PluginAuthentication().authenticate(request)


@pytest.mark.django_db
def test_plugin_authentication_inactive_user(make_organization, make_user, make_token_for_organization):
    organization = make_organization(stack_id=42, org_id=24)
    token, token_string = make_token_for_organization(organization)
    user = make_user(organization=organization, user_id=12)
    # user is set to inactive if deleted via queryset (ie. during sync)
    user.is_active = False
    user.save()

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X-Instance-Context": INSTANCE_CONTEXT,
        "HTTP_X-Grafana-Context": '{"UserId": 12}',
    }
    request = APIRequestFactory().get("/", **headers)

    with pytest.raises(AuthenticationFailed):
        PluginAuthentication().authenticate(request)


@pytest.mark.django_db
def test_plugin_authentication_gcom_setup_new_user(make_organization):
    # Setting gcom_token_org_last_time_synced to now, so it doesn't try to sync with gcom
    organization = make_organization(
        stack_id=42, org_id=24, gcom_token="123", api_token="abc", gcom_token_org_last_time_synced=timezone.now()
    )
    assert organization.users.count() == 0
    # user = make_user(organization=organization, user_id=12)

    # logged in user data available through header
    user_data = {
        "id": 12,
        "name": "Test User",
        "login": "test_user",
        "email": "test@test.com",
        "role": "Admin",
        "avatar_url": "http://test.com/avatar.png",
        "permissions": None,
        "teams": None,
    }

    headers = {
        "HTTP_AUTHORIZATION": "gcom:123",
        "HTTP_X-Instance-Context": INSTANCE_CONTEXT,
        "HTTP_X-Grafana-Context": '{"UserId": 12}',
        "HTTP_X-Oncall-User-Context": json.dumps(user_data),
    }
    request = APIRequestFactory().get("/", **headers)

    ret_user, ret_token = PluginAuthentication().authenticate(request)

    assert ret_user.user_id == 12
    assert ret_token.organization == organization
    assert organization.users.count() == 1


@pytest.mark.django_db
def test_plugin_authentication_self_hosted_setup_new_user(make_organization, make_token_for_organization):
    # Setting gcom_token_org_last_time_synced to now, so it doesn't try to sync with gcom
    organization = make_organization(stack_id=42, org_id=24)
    token, token_string = make_token_for_organization(organization)
    assert organization.users.count() == 0

    # logged in user data available through header
    user_data = {
        "id": 12,
        "name": "Test User",
        "login": "test_user",
        "email": "test@test.com",
        "role": "Admin",
        "avatar_url": "http://test.com/avatar.png",
        "permissions": None,
        "teams": None,
    }

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X-Instance-Context": INSTANCE_CONTEXT,
        "HTTP_X-Grafana-Context": '{"UserId": 12}',
        "HTTP_X-Oncall-User-Context": json.dumps(user_data),
    }
    request = APIRequestFactory().get("/", **headers)

    ret_user, ret_token = PluginAuthentication().authenticate(request)

    assert ret_user.user_id == 12
    assert ret_token.organization == organization
    assert organization.users.count() == 1
