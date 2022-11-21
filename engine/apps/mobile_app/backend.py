from push_notifications.models import APNSDevice

from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks import notify_user_async


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile app push notification"
    short_label = "Mobile app"
    available_for_use = True

    def generate_user_verification_code(self, user):
        # TODO: add QR code generation (base64 encode?), see apps.api.views.user.UserView.mobile_app_verification_token
        pass

    def unlink_user(self, user):
        # TODO: add mobile app revoke logic, see apps.api.views.user.UserView.mobile_app_verification_token
        pass

    def serialize_user(self, user):
        # TODO: add Android support using GCMDevice
        return {"connected": APNSDevice.objects.filter(user_id=user.pk).exists()}

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_async.delay(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=notification_policy.pk
        )
