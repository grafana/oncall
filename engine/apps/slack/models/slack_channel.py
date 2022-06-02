from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_slack_channel():
    prefix = "H"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while SlackChannel.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="SlackChannel"
        )
        failure_counter += 1

    return new_public_primary_key


class SlackChannel(models.Model):
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_slack_channel,
    )
    slack_id = models.CharField(max_length=100)

    slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity",
        on_delete=models.PROTECT,
        related_name="cached_channels",
        null=True,
        default=None,
    )
    name = models.CharField(max_length=500)

    is_archived = models.BooleanField(default=False)
    is_shared = models.BooleanField(null=True, default=None)
    last_populated = models.DateField(null=True, default=None)

    class Meta:
        unique_together = ("slack_id", "slack_team_identity")
