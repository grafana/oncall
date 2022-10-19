from apps.base.messaging import BaseMessagingBackend
from apps.email.tasks import notify_user_async


class EmailBackend(BaseMessagingBackend):
    backend_id = "EMAIL"
    label = "Email"
    short_label = "Email"
    available_for_use = True

    templater = "apps.email.alert_rendering.AlertEmailTemplater"
    template_fields = ("title", "message")

    def serialize_user(self, user):
        return {"email": user.email}

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_async.delay(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=notification_policy.pk
        )
