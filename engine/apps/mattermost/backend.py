from rest_framework import serializers

from apps.base.messaging import BaseMessagingBackend
from apps.mattermost.models import MattermostChannel
from apps.mattermost.tasks import notify_user_about_alert_async


class MattermostBackend(BaseMessagingBackend):
    backend_id = "MATTERMOST"
    label = "Mattermost"
    short_label = "Mattermost"
    available_for_use = True
    templater = "apps.mattermost.alert_rendering.AlertMattermostTemplater"

    def unlink_user(self, user):
        from apps.mattermost.models import MattermostUser

        mattermost_user = MattermostUser.objects.get(user=user)
        mattermost_user.delete()

    def serialize_user(self, user):
        mattermost_user = getattr(user, "mattermost_user_identity", None)
        if not mattermost_user:
            return None
        return {
            "mattermost_user_id": mattermost_user.mattermost_user_id,
            "username": mattermost_user.username,
        }

    def notify_user(self, user, alert_group, notification_policy):
        notify_user_about_alert_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
        )

    def validate_channel_filter_data(self, organization, data):
        notification_data = {}

        if not data:
            return notification_data

        if "enabled" in data:
            notification_data["enabled"] = bool(data["enabled"])

        if "channel" not in data:
            return notification_data

        # We need to treat "channel" key and "enabled" key separately
        # This condition is to handle the case when channel is cleared but the flag is enabled.
        # payload example: {"channel": nil}
        if not data["channel"]:
            notification_data["channel"] = data["channel"]
            return notification_data

        channel = MattermostChannel.objects.filter(
            organization=organization, public_primary_key=data["channel"]
        ).first()

        if not channel:
            raise serializers.ValidationError(["Invalid mattermost channel id"])

        notification_data["channel"] = channel.public_primary_key

        return notification_data
