import datetime
import enum
import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
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


class ShiftSwapRequest(models.Model):
    beneficiary: "User"
    benefactor: typing.Optional["User"]
    schedule: "OnCallSchedule"
    slack_message: typing.Optional["SlackMessage"]

    objects: models.Manager["ShiftSwapRequest"] = ShiftSwapRequestManager()
    objects_with_deleted: models.Manager["ShiftSwapRequest"] = models.Manager()

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_shift_swap_request,
    )

    created_at = models.DateTimeField(auto_now_add=True)
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
        return timezone.now() > self.swap_start

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
    def web_link(self) -> str:
        # TODO: finish this once we know the proper URL we'll need
        return f"{self.schedule.web_detail_page_link}"

    @property
    def shifts_summary(self) -> str:
        """
        This is a string summary representation of the shifts involved in this shift swap request.

        If the shift(s) start and end on the same day it will return the following format:

        `09h00 - 17h00 (UTC) on Monday July 24, 2023`

        Otherwise this format:

        `09h00 - 17h00 (UTC) from Monday July 24, 2023 until July 28, 2023`

        NOTE: For simplicity's sake, for shift swap requests that span multiple schedule events but either:
        - don't start at the beginning of the first shift (ex. starts halfway into the first shift)
        - don't end at the end of the last shift (ex. ends halfway into last shift)

        We simply exclude this info from the summary. Here's an example.

        Say we have a schedule for user A from 09h00 - 17h00 Monday - Friday. If user A opens a shift swap request
        for 12h on Monday until 17h on Friday we would still show:

        `09h00 - 17h00 (UTC) from Monday ... until Friday ...`

        The same case occurs when the `swap_end` is earlier than the last shift's end time.
        """
        shifts = self.shifts()

        def _format_time(dt: datetime.datetime) -> str:
            return dt.strftime("%Hh%M")

        def _format_date(dt: datetime.datetime) -> str:
            return dt.strftime("%a %B %-d, %Y")

        if not shifts:
            # TODO: is it possible that this could ever be a legitimate case?
            return ""

        first_shift = shifts[0]
        first_shift_start_datetime = first_shift["start"]
        first_shift_end_datetime = first_shift["end"]
        last_shift_start_datetime = first_shift["start"]
        last_shift_end_datetime = first_shift["end"]

        for shift in self.shifts():
            shift_start = shift["start"]
            shift_end = shift["end"]

            if shift_start < first_shift_start_datetime:
                first_shift_start_datetime = shift_start
                first_shift_end_datetime = shift_end

            if shift_end > last_shift_end_datetime:
                last_shift_start_datetime = shift_start
                last_shift_end_datetime = shift_end

        if first_shift_start_datetime.date() == last_shift_end_datetime.date():
            # all of the shift(s) occur on the same day
            return f"{_format_time(first_shift_start_datetime)} - {_format_time(last_shift_end_datetime)} (UTC) on {_format_date(first_shift_start_datetime)}"

        # the following two min/max usages are here to simplify the cases pertaining to a shift swap request
        # that spans several events, but:
        # - doesn't start at the beginning of the first shift (ex. starts halfway into the first shift)
        # - doesn't end at the end of the last shift  (ex. ends halfway into last shift)
        # see function docstring comment for more details
        start_time = min([first_shift_start_datetime.time(), last_shift_start_datetime.time()])
        end_time = max([first_shift_end_datetime.time(), last_shift_end_datetime.time()])

        return f"{_format_time(start_time)} - {_format_time(end_time)} (UTC) from {_format_date(first_shift_start_datetime)} until {_format_date(last_shift_end_datetime)}"

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
        # TODO: add this resource type to the insight logs public docs
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
