from apps.base.messaging import BaseMessagingBackend
from apps.mattermost.tasks import notify_user_about_alert_async


class MattermostBackend(BaseMessagingBackend):
    backend_id = "MATTERMOST"
    label = "Mattermost"
    short_label = "Mattermost"
    available_for_use = True

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
