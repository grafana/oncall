import enum
import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from apps.schedules import exceptions
from apps.schedules.tasks import refresh_ical_final_schedule
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from apps.schedules.models import OnCallSchedule
    from apps.schedules.models.on_call_schedule import ScheduleEvents
    from apps.slack.models import SlackMessage
    from apps.user_management.models import Organization, User


def generate_public_primary_key_for_shift_swap_request() -> str:
    prefix = "SSR"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while ShiftSwapRequest.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="ShiftSwapRequest"
        )
        failure_counter += 1

    return new_public_primary_key


class ShiftSwapRequestQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now())


class ShiftSwapRequestManager(models.Manager):
    def get_queryset(self):
        return ShiftSwapRequestQueryset(self.model, using=self._db).filter(deleted_at=None)

    def hard_delete(self):
        return self.get_queryset().hard_delete()

    def get_open_requests(self, now):
        return self.get_queryset().filter(benefactor__isnull=True, swap_start__gt=now)


class ShiftSwapRequest(models.Model):
    beneficiary: "User"
    benefactor: typing.Optional["User"]
    schedule: "OnCallSchedule"
    slack_message: typing.Optional["SlackMessage"]

    objects: models.Manager["ShiftSwapRequest"] = ShiftSwapRequestManager()
    objects_with_deleted: models.Manager["ShiftSwapRequest"] = models.Manager()

    FOLLOWUP_OFFSETS = [
        timezone.timedelta(weeks=4),
        timezone.timedelta(weeks=3),
        timezone.timedelta(weeks=2),
        timezone.timedelta(weeks=1),
        timezone.timedelta(days=3),
        timezone.timedelta(days=2),
        timezone.timedelta(days=1),
        timezone.timedelta(hours=12),
    ]
    """When to send followups before the swap start time"""

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_shift_swap_request,
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    schedule = models.ForeignKey(
        to="schedules.OnCallSchedule", null=False, on_delete=models.CASCADE, related_name="shift_swap_requests"
    )

    swap_start = models.DateTimeField()
    """
    so long as objects are created through the internal API, `swap_start` is guaranteed to be in UTC
    (see the internal API serializer for more details)
    """

    swap_end = models.DateTimeField()
    """
    so long as objects are created through the internal API, `swap_end` is guaranteed to be in UTC
    (see the internal API serializer for more details)
    """

    description = models.TextField(max_length=3000, default=None, null=True)

    beneficiary = models.ForeignKey(
        to="user_management.User", null=False, on_delete=models.CASCADE, related_name="created_shift_swap_requests"
    )
    """
    the person who is relieved from (part of) their shift(s)
    """

    benefactor = models.ForeignKey(
        to="user_management.User", null=True, on_delete=models.CASCADE, related_name="taken_shift_swap_requests"
    )
    """
    the person taking on shift workload from the beneficiary
    """

    slack_message = models.OneToOneField(
        "slack.SlackMessage",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="shift_swap_request",
    )
    """
    if set, represents the Slack message that was sent when the shift swap request was created
    """

    class Statuses(enum.StrEnum):
        OPEN = "open"
        TAKEN = "taken"
        PAST_DUE = "past_due"
        DELETED = "deleted"

    def __str__(self) -> str:
        return f"{self.schedule.name} {self.beneficiary.username} {self.swap_start} - {self.swap_end}"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_taken(self) -> bool:
        return self.benefactor is not None

    @property
    def is_past_due(self) -> bool:
        return not self.is_taken and timezone.now() > self.swap_start

    @property
    def is_open(self) -> bool:
        return not any((self.is_deleted, self.is_taken, self.is_past_due))

    @property
    def status(self) -> str:
        if self.is_deleted:
            return self.Statuses.DELETED
        elif self.is_taken:
            return self.Statuses.TAKEN
        elif self.is_past_due:
            return self.Statuses.PAST_DUE
        return self.Statuses.OPEN

    @property
    def slack_channel_id(self) -> str | None:
        """
        This is only set if the schedule associated with the shift swap request
        has a Slack channel configured for it.
        """
        return self.schedule.channel

    @property
    def organization(self) -> "Organization":
        return self.schedule.organization

    @property
    def possible_benefactors(self) -> QuerySet["User"]:
        return self.schedule.related_users().exclude(pk=self.beneficiary_id)

    @property
    def web_link(self) -> str:
        # TODO: finish this once we know the proper URL we'll need
        return f"{self.schedule.web_detail_page_link}"

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()
        # make sure final schedule ical representation is updated
        refresh_ical_final_schedule.apply_async((self.schedule.pk,))

    def hard_delete(self):
        super().delete()
        # make sure final schedule ical representation is updated
        refresh_ical_final_schedule.apply_async((self.schedule.pk,))

    def shifts(self) -> "ScheduleEvents":
        """Return shifts affected by this swap request."""
        schedule = typing.cast("OnCallSchedule", self.schedule.get_real_instance())
        events = schedule.final_events(self.swap_start, self.swap_end)
        related_shifts = [
            e
            for e in events
            if self.public_primary_key in set(u["swap_request"]["pk"] for u in e["users"] if u.get("swap_request"))
        ]
        return related_shifts

    def take(self, benefactor: "User") -> None:
        if benefactor == self.beneficiary:
            raise exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest()
        if self.status != self.Statuses.OPEN:
            raise exceptions.ShiftSwapRequestNotOpenForTaking()

        self.benefactor = benefactor
        self.save()

        # make sure final schedule ical representation is updated
        refresh_ical_final_schedule.apply_async((self.schedule.pk,))

    # Insight logs
    @property
    def insight_logs_verbal(self):
        return str(self)

    @property
    def insight_logs_type_verbal(self):
        return "shift_swap_request"

    @property
    def insight_logs_serialized(self):
        return {
            "description": self.description,
            "schedule": self.schedule.name,
            "swap_start": self.swap_start,
            "swap_end": self.swap_end,
            "beneficiary": self.beneficiary.username,
            "benefactor": self.benefactor.username if self.benefactor else None,
        }

    @property
    def insight_logs_metadata(self):
        return {}
