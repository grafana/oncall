import typing

from django.core.exceptions import ObjectDoesNotExist

from apps.base.messaging import BaseMessagingBackend

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.base.models import UserNotificationPolicy
    from apps.user_management.models import User


class PersonalWebhookBackend(BaseMessagingBackend):
    backend_id = "WEBHOOK"
    label = "Webhook"
    short_label = "Webhook"
    available_for_use = True

    def serialize_user(self, user: "User"):
        try:
            personal_webhook = user.personal_webhook
        except ObjectDoesNotExist:
            return None
        return {"id": personal_webhook.webhook.public_primary_key, "name": personal_webhook.webhook.name}

    def unlink_user(self, user):
        try:
            user.personal_webhook.delete()
        except ObjectDoesNotExist:
            pass

    def notify_user(
        self, user: "User", alert_group: "AlertGroup", notification_policy: typing.Optional["UserNotificationPolicy"]
    ):
        from apps.webhooks.tasks import notify_user_async

        notify_user_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk if notification_policy else None,
        )
