from unittest.mock import patch, Mock
from apps.user_webhook.tasks import notify_user_async
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.base.models import LiveSetting

import pytest


@pytest.mark.django_db
def test_fallback_to_settings(settings):
    settings.FEATURE_USER_WEBHOOK_ENABLED = True

    with patch.object(LiveSetting, "AVAILABLE_NAMES", ("FEATURE_USER_WEBHOOK_ENABLED",)):
        assert LiveSetting.get_setting("FEATURE_USER_WEBHOOK_ENABLED") is True


@patch("apps.user_webhook.tasks.requests.post", return_value=Mock(status_code=201))
@pytest.mark.django_db
def test_notify_user_failed(
    settings,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.FEATURE_USER_WEBHOOK_ENABLED = True

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=9,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    log_record = notification_policy.personal_log_records.last()
    assert log_record is None


@patch("apps.user_webhook.tasks.requests.post", return_value=Mock(status_code=400))
@pytest.mark.django_db
def test_notify_user_failed(
    settings,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.FEATURE_USER_WEBHOOK_ENABLED = True

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=9,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
