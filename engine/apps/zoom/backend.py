from rest_framework import serializers

from apps.base.messaging import BaseMessagingBackend
from apps.zoom.models import ZoomChannel
from apps.zoom.tasks import notify_user_about_alert_async


class ZoomBackend(BaseMessagingBackend):
    """
    Messaging backend for Zoom Team Chat integration.
    """
    backend_id = "ZOOM"
    label = "Zoom Team Chat"
    short_label = "Zoom"
    available_for_use = True
    templater = "apps.zoom.alert_rendering.AlertZoomTemplater"

    def unlink_user(self, user):
        """Remove Zoom link from user."""
        from apps.zoom.models import ZoomUser

        try:
            zoom_user = ZoomUser.objects.get(user=user)
            zoom_user.delete()
        except ZoomUser.DoesNotExist:
            pass

    def serialize_user(self, user):
        """Return serialized Zoom user representation."""
        zoom_user = getattr(user, "zoom_user_identity", None)
        if not zoom_user:
            return None
        return {
            "zoom_user_id": zoom_user.zoom_user_id,
            "email": zoom_user.email,
            "display_name": zoom_user.display_name,
        }

    def is_configured_for_organization(self, organization):
        """Check if Zoom is configured for the organization."""
        return ZoomChannel.objects.filter(organization=organization).exists()

    def generate_channel_verification_code(self, organization):
        """Return a verification code for a channel registration."""
        from apps.zoom.utils import ZoomEventAuthenticator
        return {
            "token": ZoomEventAuthenticator.create_token(organization),
        }

    def generate_user_verification_code(self, user):
        """Return a verification code to link a user with an account."""
        from apps.zoom.utils import ZoomEventAuthenticator
        return {
            "token": ZoomEventAuthenticator.create_token(user.organization),
        }

    def notify_user(self, user, alert_group, notification_policy):
        """Send user notification via Zoom Team Chat."""
        notify_user_about_alert_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
        )

    def validate_channel_filter_data(self, organization, data):
        """Validate JSON channel data for a channel filter update."""
        notification_data = {}

        if not data:
            return notification_data

        if "enabled" in data:
            notification_data["enabled"] = bool(data["enabled"])

        if "channel" not in data:
            return notification_data

        # Handle the case when channel is cleared but the flag is enabled
        if not data["channel"]:
            notification_data["channel"] = data["channel"]
            return notification_data

        channel = ZoomChannel.objects.filter(
            organization=organization, public_primary_key=data["channel"]
        ).first()

        if not channel:
            raise serializers.ValidationError(["Invalid Zoom channel id"])

        notification_data["channel"] = channel.public_primary_key

        return notification_data
