import typing

from apps.slack.constants import SLACK_BOT_ID
from apps.slack.scenarios import scenario_step
from apps.slack.types import EventPayload, EventType, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class ProfileUpdateStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: Any update in Slack Profile.
        Dangerous because it's often triggered by internal client's company systems.
        May cause flood, should be ready to useless updates.
        """

        member = payload["event"]["user"]
        slack_user_identity.profile_real_name = member.get("profile").get("real_name", None)
        slack_user_identity.profile_real_name_normalized = member.get("profile").get("real_name_normalized", None)
        slack_user_identity.profile_display_name = member.get("profile").get("display_name", None)
        slack_user_identity.profile_display_name_normalized = member.get("profile").get("display_name_normalized", None)
        slack_user_identity.cached_avatar = member.get("profile").get("image_512", None)
        slack_user_identity.cached_slack_email = member.get("profile").get("email", "")
        slack_user_identity.cached_timezone = member.get("tz", None)

        updated_phone_number = payload["event"]["user"]["profile"].get("phone", None)
        # if phone number was changed - drop cached number
        if updated_phone_number is None or updated_phone_number != slack_user_identity.cached_phone_number:
            slack_user_identity.cached_phone_number = None
            slack_user_identity.cached_country_code = None

        slack_user_identity.deleted = member.get("deleted", None)
        slack_user_identity.is_admin = member.get("is_admin", None)
        slack_user_identity.is_owner = member.get("is_owner", None)
        slack_user_identity.is_primary_owner = member.get("is_primary_owner", None)
        slack_user_identity.is_restricted = member.get("is_restricted", None)
        slack_user_identity.is_ultra_restricted = member.get("is_ultra_restricted", None)
        if slack_user_identity.slack_id == SLACK_BOT_ID:
            slack_user_identity.cached_is_bot = True
        else:
            slack_user_identity.cached_is_bot = member.get("is_bot", None)
        slack_user_identity.is_app_user = member.get("is_app_user", None)

        slack_user_identity.save()


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    # Slack event "user_change" is deprecated in favor of "user_profile_changed".
    # Handler for "user_change" is kept for backward compatibility.
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.USER_CHANGE,
        "step": ProfileUpdateStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.USER_PROFILE_CHANGED,
        "step": ProfileUpdateStep,
    },
]
