import typing

import humanize

from apps.slack.scenarios import scenario_step

if typing.TYPE_CHECKING:
    from apps.base.models import UserNotificationPolicy
    from apps.user_management.models import User


class EscalationDeliveryStep(scenario_step.ScenarioStep):
    """
    used for user group and channel notification in slack
    """

    def get_user_notification_message_for_thread_for_usergroup(
        self, user: "User", notification_policy: "UserNotificationPolicy"
    ) -> None:
        from apps.base.models import UserNotificationPolicy

        notification_channel = notification_policy.notify_by
        notification_step = notification_policy.step
        user_verbal = user.get_username_with_slack_verbal()
        user_verbal_with_mention = user.get_username_with_slack_verbal(mention=True)

        if (
            notification_channel == UserNotificationPolicy.NotificationChannel.SLACK
            and notification_step == UserNotificationPolicy.Step.NOTIFY
        ):
            # Mention if asked to notify by slack
            user_mention_as = user_verbal_with_mention
            notify_by = ""
        elif notification_step == UserNotificationPolicy.Step.WAIT:
            user_mention_as = user_verbal
            if notification_policy.wait_delay is not None:
                notify_by = " in {}".format(format(humanize.naturaldelta(notification_policy.wait_delay)))
            else:
                notify_by = ""
        else:
            # Don't mention if asked to notify somehow else but drop a note for colleagues
            user_mention_as = user_verbal
            notify_by = " by {}".format(UserNotificationPolicy.NotificationChannel(notification_channel).label)
        return "Inviting {}{} to look at the alert group.".format(user_mention_as, notify_by)
