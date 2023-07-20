import enum
import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

from apps.shift_swaps import exceptions
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from apps.user_management.models import User


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

    objects = ShiftSwapRequestManager()
    objects_with_deleted = models.Manager()

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
    so long as objects are created through the internal API, swap_start is guaranteed to be in UTC
    (see the internal API serializer for more details)
    """

    swap_end = models.DateTimeField()
    """
    so long as objects are created through the internal API, swap_end is guaranteed to be in UTC
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

    class Statuses(enum.StrEnum):
        OPEN = "open"
        TAKEN = "taken"
        PAST_DUE = "past_due"
        DELETED = "deleted"

    def __str__(self) -> str:
        return f"{self.schedule.name} {self.beneficiary.username} {self.swap_start} - {self.swap_end}"

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    @property
    def status(self) -> str:
        if self.deleted_at is not None:
            return self.Statuses.DELETED
        elif self.benefactor is not None:
            return self.Statuses.TAKEN
        elif timezone.now() > self.swap_start:
            return self.Statuses.PAST_DUE
        return self.Statuses.OPEN

    def take(self, benefactor: "User") -> None:
        if benefactor == self.beneficiary:
            raise exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest()
        if self.status != self.Statuses.OPEN:
            raise exceptions.ShiftSwapRequestNotOpenForTaking()

        self.benefactor = benefactor
        self.save()

        # TODO: implement the actual override logic in https://github.com/grafana/oncall/issues/2590

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
