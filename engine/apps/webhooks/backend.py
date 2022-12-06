from apps.base.messaging import BaseMessagingBackend
from .models import Webhook
from .utils import serialize_event
from .tasks import send_webhook_event


class WebhookBackend(BaseMessagingBackend):
    backend_id = "WEBHOOK"
    label = "Webhook"
    short_label = "Webhook"
    available_for_use = True

    def serialize_user(self, user):
        return {"user": user.username}

    def notify_user(self, user, alert_group, notification_policy):
        event = event = {"type": "Escalation"}
        data = serialize_event(event, alert_group, user)
        send_webhook_event.apply_async((Webhook.TRIGGER_USER_NOTIFICATION_STEP, data), {"user_id": user.id})
