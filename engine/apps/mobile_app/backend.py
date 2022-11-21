from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks import notify_user_async


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile app push notification"
    short_label = "Mobile app"
    available_for_use = True

    def serialize_user(self, user):
        return {"email": user.email}

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_async.delay(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=notification_policy.pk
        )
