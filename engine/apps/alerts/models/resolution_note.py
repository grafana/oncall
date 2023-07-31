import typing

import humanize
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from rest_framework.fields import DateTimeField

from apps.slack.slack_formatter import SlackFormatter
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length
from common.utils import clean_markup

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup


def generate_public_primary_key_for_alert_group_postmortem():
    prefix = "P"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while AlertGroupPostmortem.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="AlertGroupPostmortem"
        )
        failure_counter += 1

    return new_public_primary_key


def generate_public_primary_key_for_resolution_note():
    prefix = "M"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while ResolutionNote.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="ResolutionNote"
        )
        failure_counter += 1

    return new_public_primary_key


class ResolutionNoteSlackMessageQueryset(models.QuerySet):
    def delete(self):
        resolution_note = self.get_resolution_note()
        if resolution_note:
            resolution_note.delete()
        super().delete()


class ResolutionNoteSlackMessage(models.Model):
    alert_group: "AlertGroup"
    resolution_note: typing.Optional["ResolutionNote"]

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="resolution_note_slack_messages",
    )
    user = models.ForeignKey(
        "user_management.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="authored_resolution_note_slack_messages",
    )
    added_by_user = models.ForeignKey(
        "user_management.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="added_resolution_note_slack_messages",
    )
    text = models.TextField(max_length=3000, default=None, null=True)
    slack_channel_id = models.CharField(max_length=100, null=True, default=None)
    ts = models.CharField(max_length=100, null=True, default=None)
    thread_ts = models.CharField(max_length=100, null=True, default=None)
    permalink = models.CharField(max_length=250, null=True, default=None)
    added_to_resolution_note = models.BooleanField(default=False)
    posted_by_bot = models.BooleanField(default=False)

    class Meta:
        unique_together = ("thread_ts", "ts")

    def get_resolution_note(self) -> typing.Optional["ResolutionNote"]:
        try:
            return self.resolution_note
        except ResolutionNoteSlackMessage.resolution_note.RelatedObjectDoesNotExist:
            return None

    def delete(self, *args, **kwargs) -> typing.Tuple[int, typing.Dict[str, int]]:
        resolution_note = self.get_resolution_note()
        if resolution_note:
            resolution_note.delete()
        return super().delete(*args, **kwargs)


class ResolutionNoteQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now())

    def hard_delete(self):
        super().delete()

    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs, deleted_at__isnull=True)


class ResolutionNote(models.Model):
    alert_group: "AlertGroup"
    resolution_note_slack_message: typing.Optional[ResolutionNoteSlackMessage]

    objects = ResolutionNoteQueryset.as_manager()
    objects_with_deleted = models.Manager()

    class Source(models.IntegerChoices):
        SLACK = 0, "slack"
        WEB = 1, "web"

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_resolution_note,
    )

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="resolution_notes",
    )
    source = models.IntegerField(choices=Source.choices, default=None, null=True)
    author = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="authored_resolution_notes",
    )
    message_text = models.TextField(max_length=3000, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    resolution_note_slack_message = models.OneToOneField(
        "alerts.ResolutionNoteSlackMessage",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="resolution_note",
    )
    deleted_at = models.DateTimeField(default=None, null=True)

    def delete(self):
        ResolutionNote.objects.filter(pk=self.pk).delete()

    def hard_delete(self):
        super().delete()

    @property
    def text(self):
        if self.source == ResolutionNote.Source.SLACK:
            return self.resolution_note_slack_message.text
        return self.message_text

    def recreate(self):
        """
        Recreates soft-deleted resolution note.
        E.g. resolution note can be removed and then added again in slack.
        """
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    def render_log_line_json(self):
        time = humanize.naturaldelta(self.alert_group.started_at - self.created_at)
        created_at = DateTimeField().to_representation(self.created_at)
        author = self.author.short() if self.author is not None else None

        sf = SlackFormatter(self.alert_group.channel.organization)
        action = sf.format(self.text)
        action = clean_markup(action)

        result = {
            "time": time,
            "action": action,
            "realm": "resolution_note",
            "type": self.source,
            "created_at": created_at,
            "author": author,
        }

        return result

    def author_verbal(self, mention):
        """
        Postmortems to resolution notes included migrating AlertGroupPostmortem to ResolutionNotes.
        But AlertGroupPostmortem has no author field. So this method was introduces as workaround.
        """
        if self.author is not None:
            return self.author.get_username_with_slack_verbal(mention)
        else:
            return ""


class AlertGroupPostmortem(models.Model):
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_alert_group_postmortem,
    )
    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="postmortem_text",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    text = models.TextField(max_length=3000, default=None, null=True)
