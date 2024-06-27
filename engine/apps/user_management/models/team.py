import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroupLogRecord
    from apps.schedules.models import CustomOnCallShift
    from apps.user_management.models import User


def generate_public_primary_key_for_team() -> str:
    prefix = "T"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Team.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Team"
        )
        failure_counter += 1

    return new_public_primary_key


class TeamManager(models.Manager["Team"]):
    pass


class Team(models.Model):
    current_team_users: "RelatedManager['User']"
    custom_on_call_shifts: "RelatedManager['CustomOnCallShift']"
    oncall_schedules: "RelatedManager['AlertGroupLogRecord']"
    users: "RelatedManager['User']"

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

    class Meta:
        unique_together = ("organization", "team_id")
