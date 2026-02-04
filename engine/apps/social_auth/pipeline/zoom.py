from apps.social_auth.backends import ZOOM_LOGIN_BACKEND
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


def connect_user_to_zoom(response, backend, strategy, user, organization, *args, **kwargs):
    """
    Pipeline step to connect OnCall user to their Zoom account.
    
    This is called after successful OAuth authentication with Zoom.
    """
    from apps.zoom.models import ZoomUser

    if backend.name != ZOOM_LOGIN_BACKEND:
        return

    # At this point everything is correct and we can create the ZoomUser
    # Clear any pre-existing sessions to avoid showing stale errors
    strategy.session.flush()

    ZoomUser.objects.update_or_create(
        user=user,
        defaults={
            "zoom_user_id": response["user"]["user_id"],
            "email": response["user"]["email"],
            "display_name": response["user"]["display_name"],
        },
    )

    write_chatops_insight_log(
        author=user,
        event_name=ChatOpsEvent.USER_LINKED,
        chatops_type=ChatOpsTypePlug.ZOOM.value,
        linked_user=user.username,
        linked_user_id=user.public_primary_key,
    )
