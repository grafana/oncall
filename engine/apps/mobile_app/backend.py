from push_notifications.models import APNSDevice

from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks import notify_user_async


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile app push notification"
    short_label = "Mobile app"
    available_for_use = True

    # TODO: add QR code generation (base64 encode?)
    def generate_user_verification_code(self, user):
        from apps.mobile_app.models import MobileAppVerificationToken

        # remove existing token before creating a new one
        MobileAppVerificationToken.objects.filter(user=user).delete()

        _, token = MobileAppVerificationToken.create_auth_token(user, user.organization)
        return token

    def unlink_user(self, user):
        from apps.mobile_app.models import MobileAppVerificationToken

        token = MobileAppVerificationToken.objects.get(user=user)
        token.delete()

    def serialize_user(self, user):
        # TODO: add Android support using GCMDevice
        return {"connected": APNSDevice.objects.filter(user_id=user.pk).exists()}

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_async.delay(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=notification_policy.pk
        )
