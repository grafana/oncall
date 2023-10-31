import typing

from rest_framework import serializers

from apps.schedules.ical_utils import SchedulesOnCallUsers
from apps.user_management.models import Team


class TeamSerializerContext(typing.TypedDict):
    schedules_with_oncall_users: SchedulesOnCallUsers


class FastTeamSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Team
        fields = ["id", "name", "email", "avatar_url"]


class TeamSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "email",
            "avatar_url",
            "is_sharing_resources_to_all",
            "number_of_users_currently_oncall",
        ]

        read_only_fields = [
            "id",
            "name",
            "email",
            "avatar_url",
        ]


class TeamLongSerializer(TeamSerializer):
    context: TeamSerializerContext

    number_of_users_currently_oncall = serializers.SerializerMethodField()

    class Meta(TeamSerializer.Meta):
        fields = TeamSerializer.Meta.fields + [
            "number_of_users_currently_oncall",
        ]

    def get_number_of_users_currently_oncall(self, obj: Team) -> int:
        num_of_users_oncall_for_team = 0

        for schedule, users in self.context["schedules_with_oncall_users"].items():
            if schedule.team == obj:
                num_of_users_oncall_for_team += len(users)

        return num_of_users_oncall_for_team
