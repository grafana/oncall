import typing

from django.utils import timezone

from apps.slack.scenarios import scenario_step
from apps.slack.types import EventPayload, EventType, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class SlackUserGroupEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: creation user groups or changes in user groups except its members.
        """
        from apps.slack.models import SlackUserGroup

        slack_id = payload["event"]["subteam"]["id"]
        usergroup_name = payload["event"]["subteam"]["name"]
        usergroup_handle = payload["event"]["subteam"]["handle"]
        members = payload["event"]["subteam"].get("users", [])
        is_active = payload["event"]["subteam"]["date_delete"] == 0

        SlackUserGroup.objects.update_or_create(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
            defaults={
                "name": usergroup_name,
                "handle": usergroup_handle,
                "members": members,
                "is_active": is_active,
                "last_populated": timezone.now().date(),
            },
        )


class SlackUserGroupMembersChangedEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: changed members in user group.
        """
        from apps.slack.models import SlackUserGroup

        slack_id = payload["event"]["subteam_id"]
        try:
            user_group = slack_team_identity.usergroups.get(slack_id=slack_id)
        except SlackUserGroup.DoesNotExist:
            # If Slack group does not exist, create and populate it
            SlackUserGroup.update_or_create_slack_usergroup_from_slack(slack_id, slack_team_identity)
        else:
            # else update its members from payload
            members = set(user_group.members)
            members_added = payload["event"]["added_users"]
            members_removed = payload["event"]["removed_users"]
            members.update(members_added)
            members.difference_update(members_removed)

            user_group.members = list(members)
            user_group.save(update_fields=["members"])


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.SUBTEAM_CREATED,
        "step": SlackUserGroupEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.SUBTEAM_UPDATED,
        "step": SlackUserGroupEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.SUBTEAM_MEMBERS_CHANGED,
        "step": SlackUserGroupMembersChangedEventStep,
    },
]
