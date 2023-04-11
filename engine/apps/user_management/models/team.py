from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_team():
    prefix = "T"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Team.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Team"
        )
        failure_counter += 1

    return new_public_primary_key


class TeamManager(models.Manager):
    @staticmethod
    def sync_for_organization(organization, api_teams: list[dict]):
        grafana_teams = {team["id"]: team for team in api_teams}
        existing_team_ids = set(organization.teams.all().values_list("team_id", flat=True))

        # create missing teams
        teams_to_create = tuple(
            Team(
                organization_id=organization.pk,
                team_id=team["id"],
                name=team["name"],
                email=team["email"],
                avatar_url=team["avatarUrl"],
            )
            for team in grafana_teams.values()
            if team["id"] not in existing_team_ids
        )
        organization.teams.bulk_create(teams_to_create, batch_size=5000)

        # delete excess teams
        team_ids_to_delete = existing_team_ids - grafana_teams.keys()
        organization.teams.filter(team_id__in=team_ids_to_delete).delete()

        # update existing teams if any fields have changed
        teams_to_update = []
        for team in organization.teams.filter(team_id__in=existing_team_ids):
            grafana_team = grafana_teams[team.team_id]
            if (
                team.name != grafana_team["name"]
                or team.email != grafana_team["email"]
                or team.avatar_url != grafana_team["avatarUrl"]
            ):
                team.name = grafana_team["name"]
                team.email = grafana_team["email"]
                team.avatar_url = grafana_team["avatarUrl"]
                teams_to_update.append(team)
        organization.teams.bulk_update(teams_to_update, ["name", "email", "avatar_url"], batch_size=5000)


class Team(models.Model):
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_team,
    )

    objects = TeamManager()

    team_id = models.PositiveIntegerField()
    organization = models.ForeignKey(
        to="user_management.Organization",
        related_name="teams",
        on_delete=models.deletion.CASCADE,
    )
    users = models.ManyToManyField(to="user_management.User", related_name="teams")
    name = models.CharField(max_length=300)
    email = models.CharField(max_length=300, null=True, blank=True, default=None)
    avatar_url = models.URLField()

    # If is_sharing_resources_to_all is False only team members and admins can access it and it's resources
    # if it's True every oncall organization user can access it
    is_sharing_resources_to_all = models.BooleanField(default=False)
