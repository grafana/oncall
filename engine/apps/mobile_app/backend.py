import json

from django.conf import settings

from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks import notify_user_async


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile push"
    short_label = "Mobile push"
    available_for_use = True
    template_fields = ["title"]

    def generate_user_verification_code(self, user):
        from apps.mobile_app.models import MobileAppVerificationToken

        # remove existing token before creating a new one
        MobileAppVerificationToken.objects.filter(user=user).delete()

        _, token = MobileAppVerificationToken.create_auth_token(user, user.organization)
        return json.dumps(
            {
                "token": token,
                "oncall_api_url": settings.BASE_URL,
            }
        )

    def unlink_user(self, user):
        from apps.mobile_app.models import FCMDevice, MobileAppAuthToken

        token = MobileAppAuthToken.objects.get(user=user)
        token.delete()

        # delete push notification related info for user
        user_active_device = FCMDevice.get_active_device_for_user(user)
        if user_active_device is not None:
            user_active_device.delete()

    def serialize_user(self, user):
        from apps.mobile_app.models import MobileAppAuthToken

        return {"connected": MobileAppAuthToken.objects.filter(user=user).exists()}

    def notify_user(self, user, alert_group, notification_policy, critical=False):
        notify_user_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=critical,
        )

    @property
    def customizable_templates(self):
        """
        Disable customization if templates for mobile app
        """
        return False


class MobileAppCriticalBackend(MobileAppBackend):
    """
    This notification backend should not exist, criticality of the push notification should be an option passed to the
    MobileAppBackend messaging backend.
    TODO: add ability to pass options to messaging backends both on backend and frontend, delete this backend after that
    """

    backend_id = "MOBILE_APP_CRITICAL"
    label = "Mobile push important"
    short_label = "Mobile push important"
    template_fields = []

    def notify_user(self, user, alert_group, notification_policy, critical=True):
        super().notify_user(user, alert_group, notification_policy, critical)
