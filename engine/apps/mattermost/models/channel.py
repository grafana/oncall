from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_mattermost_channel():
    prefix = "MT"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while MattermostChannel.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="MattermostChannel"
        )
        failure_counter += 1

    return new_public_primary_key


class MattermostChannel(models.Model):
    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="mattermost_channels",
    )

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_mattermost_channel,
    )

    channel_id = models.CharField(max_length=100, default=None)
    channel_name = models.CharField(max_length=100, default=None)
    display_name = models.CharField(max_length=100, default=None)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "channel_id")
