import json

from django.conf import settings

from apps.base.messaging import BaseMessagingBackend
from apps.mobile_app.tasks.new_alert_group import notify_user_about_new_alert_group


class MobileAppBackend(BaseMessagingBackend):
    backend_id = "MOBILE_APP"
    label = "Mobile push"
    short_label = "Mobile push"
    available_for_use = True

    templater = "apps.mobile_app.alert_rendering.AlertMobileAppTemplater"
    template_fields = ("title", "message")
    skip_default_template_fields = True

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
        return {"connected": getattr(user, "mobileappauthtoken", None) is not None}

    def notify_user(self, user, alert_group, notification_policy, critical=False):
        notify_user_about_new_alert_group.delay(
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
    label = "Mobile push important"
    short_label = "Mobile push important"
    template_fields = []

    def notify_user(self, user, alert_group, notification_policy, critical=True):
        super().notify_user(user, alert_group, notification_policy, critical)
