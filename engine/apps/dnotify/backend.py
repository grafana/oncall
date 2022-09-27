from apps.base.messaging import BaseMessagingBackend

BACKEND_ID = "DESKTOPDEMO"


class DesktopBackend(BaseMessagingBackend):
    backend_id = BACKEND_ID
    label = "Desktop Notifications"
    short_label = "Desktop"
    available_for_use = True
    templater = "apps.dnotify.alert_rendering.AlertNotifyTemplater"

    def validate_channel_filter_data(self, organization, data):
        """Validate channel route selection updates."""
        # see engine/apps/public_api/serializers/routes.py
        # engine/apps/api/serializers/channel_filter.py
        return data

    def serialize_user(self, user):
        """Return serialized representation of the backend user."""
        return user.username

    def notify_user(self, user, alert_group, notification_policy):
        """Trigger async task to notify user about alert."""
        from .tasks import notify_user_async

        notify_user_async.apply_async((alert_group.pk, user.pk))
