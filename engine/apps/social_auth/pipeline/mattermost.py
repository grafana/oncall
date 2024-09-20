from apps.social_auth.backends import MATTERMOST_LOGIN_BACKEND
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


def connect_user_to_mattermost(response, backend, strategy, user, organization, *args, **kwargs):
    from apps.mattermost.models import MattermostUser

    if backend.name != MATTERMOST_LOGIN_BACKEND:
        return

    # at this point everything is correct and we can create the MattermostUser
    # be sure to clear any pre-existing sessions, in case the user previously enecountered errors we want
    # to be sure to clear these so they do not see them again
    strategy.session.flush()

    MattermostUser.objects.get_or_create(
        user=user,
        mattermost_user_id=response["user"]["user_id"],
        defaults={
            "username": response["user"]["username"],
            "nickname": response["user"]["nickname"],
        },
    )

    write_chatops_insight_log(
        author=user,
        event_name=ChatOpsEvent.USER_LINKED,
        chatops_type=ChatOpsTypePlug.MATTERMOST.value,
        linked_user=user.username,
        linked_user_id=user.public_primary_key,
    )
