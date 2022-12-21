from apps.base.messaging import BaseMessagingBackend
from apps.user_webhook.tasks import notify_user_async


class UserWebhookBackend(BaseMessagingBackend):
    backend_id = "USER_WEBHOOK"
    label = "Webhook"
    short_label = "Webhook"
    available_for_use = True

    def serialize_user(self, user):
        return {"email": user.email}

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_async.delay(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=notification_policy.pk
        )
