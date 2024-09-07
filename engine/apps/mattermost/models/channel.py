from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction

from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log
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

    mattermost_team_id = models.CharField(max_length=100, default=None)
    channel_id = models.CharField(max_length=100, default=None)
    channel_name = models.CharField(max_length=100, default=None)
    display_name = models.CharField(max_length=100, default=None)
    is_default_channel = models.BooleanField(null=True, default=False)
    datetime = models.DateTimeField(auto_now_add=True)

    @property
    def unique_display_name(self) -> str:
        return f"{self.display_name}-{self.mattermost_team_id[:5]}"

    class Meta:
        unique_together = ("organization", "channel_id")

    def make_channel_default(self, author):
        try:
            old_default_channel = MattermostChannel.objects.get(organization=self.organization, is_default_channel=True)
            old_default_channel.is_default_channel = False
        except MattermostChannel.DoesNotExist:
            old_default_channel = None
            self.is_default_channel = True
            self.save(update_fields=["is_default_channel"])
        else:
            self.is_default_channel = True
            with transaction.atomic():
                old_default_channel.save(update_fields=["is_default_channel"])
                self.save(update_fields=["is_default_channel"])

        print(f"Model: {self.is_default_channel}")
        write_chatops_insight_log(
            author=author,
            event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
            chatops_type=ChatOpsTypePlug.MATTERMOST.value,
            prev_channel=old_default_channel.channel_name if old_default_channel else None,
            new_channel=self.channel_name,
        )
