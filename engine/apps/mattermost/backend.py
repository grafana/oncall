from apps.base.messaging import BaseMessagingBackend


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
        mattermost_user = getattr(user, "mattermost_connection", None)
        if not mattermost_user:
            return None
        return {
            "mattermost_user_id": mattermost_user.mattermost_user_id,
            "username": mattermost_user.username,
        }
