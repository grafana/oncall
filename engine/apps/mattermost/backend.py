from apps.base.messaging import BaseMessagingBackend

BACKEND_ID = "MATTERMOST"


class MattermostBackend(BaseMessagingBackend):
    backend_id = BACKEND_ID
    label = "Mattermost"
    short_label = "Mattermost"
    available_for_use = True
    templater = "apps.mattermost.alert_rendering.AlertMattermostTemplater"

    def validate_channel_filter_data(self, organization, data):
        """Validate channel route selection updates."""
        # TODO: check this is a valid channel for organization
        return data

    def serialize_user(self, user):
        """Return serialized representation of the backend user."""
        # TODO: return a mattermost user representation
        # (it will be used by frontend, in the user profile)
        return {"username": ""}

    def notify_user(self, user, alert_group, notification_policy):
        """Trigger async task to notify user about alert."""
        # TODO: check this is a backend user
        from .tasks import notify_user_async

        notify_user_async.apply_async((alert_group.pk, user.pk))
