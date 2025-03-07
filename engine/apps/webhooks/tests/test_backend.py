from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.base.models import UserNotificationPolicy
from apps.webhooks.backend import PersonalWebhookBackend
from apps.webhooks.models import Webhook


@pytest.mark.django_db
def test_serialize_user(
    make_organization, make_user_for_organization, make_custom_webhook, make_personal_notification_webhook
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    backend = PersonalWebhookBackend()

    # by default, there is no personal webhook set
    assert backend.serialize_user(user) is None

    # set personal webhook
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_PERSONAL_NOTIFICATION,
    )
    make_personal_notification_webhook(user=user, webhook=webhook)

    assert backend.serialize_user(user) == {"id": webhook.public_primary_key, "name": webhook.name}


@pytest.mark.django_db
def test_unlink_webhook(
    make_organization,
    make_user_for_organization,
    make_custom_webhook,
    make_personal_notification_webhook,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    backend = PersonalWebhookBackend()
    # set personal webhook
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_PERSONAL_NOTIFICATION,
    )
    make_personal_notification_webhook(user=user, webhook=webhook)

    assert user.personal_webhook is not None

    backend.unlink_user(user)
    user.refresh_from_db()
    with pytest.raises(ObjectDoesNotExist):
        user.personal_webhook


@pytest.mark.django_db
def test_notify_user_triggers_task(
    make_organization,
    make_user_for_organization,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    make_personal_notification_webhook,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    backend = PersonalWebhookBackend()
    # set personal webhook
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_PERSONAL_NOTIFICATION,
    )
    make_personal_notification_webhook(user=user, webhook=webhook)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=settings.PERSONAL_WEBHOOK_BACKEND_ID,
        important=False,
    )

    with patch("apps.webhooks.tasks.notify_user_async") as mock_notify_user_async:
        backend.notify_user(user, alert_group, notification_policy)

    mock_notify_user_async.delay.assert_called_once_with(
        user_pk=user.pk,
        alert_group_pk=alert_group.pk,
        notification_policy_pk=notification_policy.pk,
    )
