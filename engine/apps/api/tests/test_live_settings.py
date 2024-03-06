from unittest import mock

import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from apps.base.models import LiveSetting


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


@pytest.mark.django_db
def test_live_settings_update_validate_settings_once(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_live_setting,
    settings,
):
    """
    Check that settings are validated only once per update.
    """

    settings.FEATURE_LIVE_SETTINGS_ENABLED = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    LiveSetting.populate_settings_if_needed()
    live_setting = LiveSetting.objects.get(name="EMAIL_HOST")  # random setting

    client = APIClient()
    url = reverse("api-internal:live_settings-detail", kwargs={"pk": live_setting.public_primary_key})
    data = {"id": live_setting.public_primary_key, "value": "TEST_UPDATED_VALUE", "name": "EMAIL_HOST"}

    with mock.patch.object(LiveSetting, "validate_settings") as mock_validate_settings:
        response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == HTTP_200_OK
    mock_validate_settings.assert_called_once()


@pytest.mark.django_db
def test_live_settings_telegram_calls_set_webhook_once(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_live_setting,
    settings,
):
    """
    Check that when TELEGRAM_WEBHOOK_HOST live setting is updated, set_webhook method is called only once.
    If set_webhook is called more than once in a short period of time, there will be a rate limit error.
    """

    settings.FEATURE_LIVE_SETTINGS_ENABLED = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    LiveSetting.populate_settings_if_needed()
    live_setting = LiveSetting.objects.get(name="TELEGRAM_WEBHOOK_HOST")

    client = APIClient()
    url = reverse("api-internal:live_settings-detail", kwargs={"pk": live_setting.public_primary_key})
    data = {"id": live_setting.public_primary_key, "value": "TEST_UPDATED_VALUE", "name": "TELEGRAM_WEBHOOK_HOST"}

    with mock.patch("telegram.Bot.get_webhook_info", return_value=mock.Mock(url="TEST_VALUE")):
        with mock.patch("telegram.Bot.set_webhook") as mock_set_webhook:
            response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == HTTP_200_OK
    mock_set_webhook.assert_called_once_with(
        "TEST_UPDATED_VALUE/telegram/", allowed_updates=("message", "callback_query")
    )


@pytest.mark.django_db
def test_live_settings_telegram_set_webhook_not_called_if_long_polling_enabled(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_live_setting,
    settings,
):
    """
    Check that when FEATURE_TELEGRAM_LONG_POLLING_ENABLED is true setting webhook with updating
    TELEGRAM_WEBHOOK_HOST live setting does not evaluate.
    """

    settings.FEATURE_LIVE_SETTINGS_ENABLED = True
    settings.FEATURE_TELEGRAM_LONG_POLLING_ENABLED = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    LiveSetting.populate_settings_if_needed()
    live_setting = LiveSetting.objects.get(name="TELEGRAM_WEBHOOK_HOST")

    client = APIClient()
    url = reverse("api-internal:live_settings-detail", kwargs={"pk": live_setting.public_primary_key})
    data = {"id": live_setting.public_primary_key, "value": "TEST_UPDATED_VALUE", "name": "TELEGRAM_WEBHOOK_HOST"}

    with mock.patch("telegram.Bot.set_webhook") as mock_set_webhook:
        response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == HTTP_200_OK
    mock_set_webhook.assert_not_called()
