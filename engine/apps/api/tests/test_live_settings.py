from unittest import mock

import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_list_live_setting(
    make_organization_and_user_with_slack_identities,
    make_user_auth_headers,
    make_token_for_organization,
    settings,
):
    settings.FEATURE_LIVE_SETTINGS_ENABLED = True

    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:live_settings-list")

    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == HTTP_200_OK


@mock.patch("apps.slack.tasks.unpopulate_slack_user_identities.apply_async", return_value=None)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "setting_name",
    [
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
    ],
)
def test_live_settings_update_trigger_unpopulate_slack_identities(
    mocked_unpopulate_task,
    make_organization_and_user_with_slack_identities,
    make_user_auth_headers,
    make_token_for_organization,
    make_live_setting,
    settings,
    setting_name,
):
    settings.FEATURE_LIVE_SETTINGS_ENABLED = True

    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    setattr(settings, setting_name, "default_setting_value")
    client = APIClient()
    live_setting = make_live_setting(name=setting_name, value="default_setting_value")
    url = reverse("api-internal:live_settings-detail", kwargs={"pk": live_setting.public_primary_key})
    data_to_put = {
        "id": live_setting.public_primary_key,
        "value": "987654321987.987654321987",
        "name": setting_name,
    }
    response = client.put(url, data=data_to_put, format="json", **make_user_auth_headers(user, token))
    assert mocked_unpopulate_task.called

    assert response.status_code == HTTP_200_OK


@mock.patch("apps.slack.tasks.unpopulate_slack_user_identities.apply_async", return_value=None)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "setting_name",
    [
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
    ],
)
def test_live_settings_update_not_trigger_unpopulate_slack_identities(
    mocked_unpopulate_task,
    make_organization_and_user_with_slack_identities,
    make_user_auth_headers,
    make_token_for_organization,
    make_live_setting,
    settings,
    setting_name,
):
    settings.FEATURE_LIVE_SETTINGS_ENABLED = True

    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    setattr(settings, setting_name, "default_setting_value")
    client = APIClient()
    live_setting = make_live_setting(name=setting_name, value="default_setting_value")
    url = reverse("api-internal:live_settings-detail", kwargs={"pk": live_setting.public_primary_key})
    data_to_put = {
        "id": live_setting.public_primary_key,
        "value": "default_setting_value",
        "name": setting_name,
    }
    response = client.put(url, data=data_to_put, format="json", **make_user_auth_headers(user, token))
    assert not mocked_unpopulate_task.called

    assert response.status_code == HTTP_200_OK
