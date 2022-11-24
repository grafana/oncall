from push_notifications.models import APNSDevice

from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks import notify_user_async


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile app"
    short_label = "Mobile app"
    available_for_use = True
    template_fields = ["title"]

    # TODO: add QR code generation (base64 encode?)
    def generate_user_verification_code(self, user):
        from apps.mobile_app.models import MobileAppVerificationToken

        # remove existing token before creating a new one
        MobileAppVerificationToken.objects.filter(user=user).delete()

        _, token = MobileAppVerificationToken.create_auth_token(user, user.organization)
        return token

    def unlink_user(self, user):
        from apps.mobile_app.models import MobileAppAuthToken

        token = MobileAppAuthToken.objects.get(user=user)
        token.delete()

    def serialize_user(self, user):
        # TODO: add Android support using GCMDevice
        return {"connected": APNSDevice.objects.filter(user_id=user.pk).exists()}

    def notify_user(self, user, alert_group, notification_policy, critical=False):
        notify_user_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=critical,
        )


class MobileAppCriticalBackend(MobileAppBackend):
    """
    This notification backend should not exist, criticality of the push notification should be an option passed to the
    MobileAppBackend messaging backend.
    TODO: add ability to pass options to messaging backends both on backend and frontend, delete this backend after that
    """

    backend_id = "MOBILE_APP_CRITICAL"
    label = "Mobile app critical"
    short_label = "Mobile app critical"
    template_fields = []

    def notify_user(self, user, alert_group, notification_policy, critical=True):
        super().notify_user(user, alert_group, notification_policy, critical)
