import datetime
from enum import unique
from typing import Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import IntegrityError, models
from django.db.models import Q

from apps.base.messaging import get_messaging_backends
from apps.user_management.models import User
from common.exceptions import UserNotificationPolicyCouldNotBeDeleted
from common.ordered_model.ordered_model import OrderedModel
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_notification_policy():
    prefix = "N"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while UserNotificationPolicy.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="UserNotificationPolicy"
        )
        failure_counter += 1

    return new_public_primary_key


# base supported notification backends
BUILT_IN_BACKENDS = (
    ("SLACK", 0),
    ("SMS", 1),
    ("PHONE_CALL", 2),
    ("TELEGRAM", 3),
)


def _notification_channel_choices():
    """Return dynamically built choices for available notification channel backends."""

    # Enum containing notification channel choices on the database level.
    # Also see NotificationChannelOptions class with more logic on notification channels.
    # Do not remove items from this enum if you just want to disable a notification channel temporarily,
    # use NotificationChannelOptions.AVAILABLE_FOR_USE instead.
    supported_backends = list(BUILT_IN_BACKENDS)

    for backend_id, backend in get_messaging_backends():
        supported_backends.append((backend_id, backend.notification_channel_id))

    channels_enum = unique(models.IntegerChoices("NotificationChannel", supported_backends))
    return channels_enum


_notification_channels = _notification_channel_choices()


def validate_channel_choice(value):
    if value is None:
        return
    try:
        _notification_channels(value)
    except ValueError:
        raise ValidationError("%(value)s is not a valid option", params={"value": value})


class UserNotificationPolicyQuerySet(models.QuerySet):
    def create_default_policies_for_user(self, user: User) -> None:
        if user.notification_policies.filter(important=False).exists():
            return

        model = self.model
        policies_to_create = (
            model(
                user=user,
                step=model.Step.NOTIFY,
                notify_by=NotificationChannelOptions.DEFAULT_NOTIFICATION_CHANNEL,
                order=0,
            ),
            model(user=user, step=model.Step.WAIT, wait_delay=datetime.timedelta(minutes=15), order=1),
            model(user=user, step=model.Step.NOTIFY, notify_by=model.NotificationChannel.PHONE_CALL, order=2),
        )

        try:
            super().bulk_create(policies_to_create)
        except IntegrityError:
            pass

    def create_important_policies_for_user(self, user: User) -> None:
        if user.notification_policies.filter(important=True).exists():
            return

        model = self.model
        policies_to_create = (
            model(
                user=user,
                step=model.Step.NOTIFY,
                notify_by=model.NotificationChannel.PHONE_CALL,
                important=True,
                order=0,
            ),
        )

        try:
            super().bulk_create(policies_to_create)
        except IntegrityError:
            pass


class UserNotificationPolicy(OrderedModel):
    objects = UserNotificationPolicyQuerySet.as_manager()
    order_with_respect_to = ("user_id", "important")

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_notification_policy,
    )

    user = models.ForeignKey(
        "user_management.User", on_delete=models.CASCADE, related_name="notification_policies", default=None, null=True
    )

    class Step(models.IntegerChoices):
        WAIT = 0, "Wait"
        NOTIFY = 1, "Notify by"

    step = models.PositiveSmallIntegerField(choices=Step.choices, default=None, null=True)

    NotificationChannel = _notification_channels
    notify_by = models.PositiveSmallIntegerField(default=0, validators=[validate_channel_choice])

    ONE_MINUTE = datetime.timedelta(minutes=1)
    FIVE_MINUTES = datetime.timedelta(minutes=5)
    FIFTEEN_MINUTES = datetime.timedelta(minutes=15)
    THIRTY_MINUTES = datetime.timedelta(minutes=30)
    HOUR = datetime.timedelta(minutes=60)

    DURATION_CHOICES = (
        (ONE_MINUTE, "1 min"),
        (FIVE_MINUTES, "5 min"),
        (FIFTEEN_MINUTES, "15 min"),
        (THIRTY_MINUTES, "30 min"),
        (HOUR, "60 min"),
    )

    wait_delay = models.DurationField(default=None, null=True, choices=DURATION_CHOICES)

    important = models.BooleanField(default=False)

    class Meta:
        ordering = ("order",)
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "important", "order"], name="unique_user_notification_policy_order"
            )
        ]

    def __str__(self):
        return f"{self.pk}: {self.short_verbal}"

    @classmethod
    def get_short_verbals_for_user(cls, user: User) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        is_wait_step = Q(step=cls.Step.WAIT)
        is_wait_step_configured = Q(wait_delay__isnull=False)

        policies = cls.objects.filter(Q(user=user, step__isnull=False) & (~is_wait_step | is_wait_step_configured))

        default = tuple(str(policy.short_verbal) for policy in policies if policy.important is False)
        important = tuple(str(policy.short_verbal) for policy in policies if policy.important is True)

        return default, important

    @property
    def short_verbal(self) -> str:
        if self.step == UserNotificationPolicy.Step.NOTIFY:
            try:
                notification_channel = self.NotificationChannel(self.notify_by)
            except ValueError:
                return "Not set"
            return NotificationChannelAPIOptions.SHORT_LABELS[notification_channel]
        elif self.step == UserNotificationPolicy.Step.WAIT:
            if self.wait_delay is None:
                return "0 min"
            else:
                return self.get_wait_delay_display()
        else:
            return "Not set"

    def delete(self):
        if UserNotificationPolicy.objects.filter(important=self.important, user=self.user).count() == 1:
            raise UserNotificationPolicyCouldNotBeDeleted("Can't delete last user notification policy")
        else:
            super().delete()


class NotificationChannelOptions:
    """
    NotificationChannelOptions encapsulates logic of notification channel representation for API and public API,
    integration constraints and contains a list of available notification channels.

    To prohibit using a notification channel, remove it from AVAILABLE_FOR_USE list.
    Note that removing a notification channel from AVAILABLE_FOR_USE removes it from API and public API,
    but doesn't change anything in the database.
    """

    AVAILABLE_FOR_USE = [
        UserNotificationPolicy.NotificationChannel.SLACK,
        UserNotificationPolicy.NotificationChannel.SMS,
        UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        UserNotificationPolicy.NotificationChannel.TELEGRAM,
    ] + [
        getattr(UserNotificationPolicy.NotificationChannel, backend_id)
        for backend_id, b in get_messaging_backends()
        if b.available_for_use
    ]

    DEFAULT_NOTIFICATION_CHANNEL = UserNotificationPolicy.NotificationChannel.SLACK

    SLACK_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [UserNotificationPolicy.NotificationChannel.SLACK]
    TELEGRAM_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [UserNotificationPolicy.NotificationChannel.TELEGRAM]


class NotificationChannelAPIOptions(NotificationChannelOptions):
    LABELS = {
        UserNotificationPolicy.NotificationChannel.SLACK: "Slack mentions",
        UserNotificationPolicy.NotificationChannel.SMS: "SMS \U00002709\U0001F4F2",
        UserNotificationPolicy.NotificationChannel.PHONE_CALL: "Phone call \U0000260E",
        UserNotificationPolicy.NotificationChannel.TELEGRAM: "Telegram \U0001F916",
    }
    LABELS.update(
        {
            getattr(UserNotificationPolicy.NotificationChannel, backend_id): b.label
            for backend_id, b in get_messaging_backends()
        }
    )

    SHORT_LABELS = {
        UserNotificationPolicy.NotificationChannel.SLACK: "Slack",
        UserNotificationPolicy.NotificationChannel.SMS: "SMS",
        UserNotificationPolicy.NotificationChannel.PHONE_CALL: "\U0000260E",
        UserNotificationPolicy.NotificationChannel.TELEGRAM: "Telegram",
    }
    SHORT_LABELS.update(
        {
            getattr(UserNotificationPolicy.NotificationChannel, backend_id): b.short_label
            for backend_id, b in get_messaging_backends()
        }
    )


class NotificationChannelPublicAPIOptions(NotificationChannelAPIOptions):
    LABELS = {
        UserNotificationPolicy.NotificationChannel.SLACK: "notify_by_slack",
        UserNotificationPolicy.NotificationChannel.SMS: "notify_by_sms",
        UserNotificationPolicy.NotificationChannel.PHONE_CALL: "notify_by_phone_call",
        UserNotificationPolicy.NotificationChannel.TELEGRAM: "notify_by_telegram",
    }
    LABELS.update(
        {
            getattr(UserNotificationPolicy.NotificationChannel, backend_id): "notify_by_{}".format(b.slug)
            for backend_id, b in get_messaging_backends()
        }
    )
