from typing import Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from ordered_model.models import OrderedModel

from apps.base.messaging import get_messaging_backends
from apps.user_management.models import User
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
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
    "SLACK",
    "SMS",
    "PHONE_CALL",
    "TELEGRAM",
    "EMAIL",
    "MOBILE_PUSH_GENERAL",
    "MOBILE_PUSH_CRITICAL",
)


def _notification_channel_choices():
    """Return dynamically built choices for available notification channel backends."""

    # Enum containing notification channel choices on the database level.
    # Also see NotificationChannelOptions class with more logic on notification channels.
    # Do not remove items from this enum if you just want to disable a notification channel temporarily,
    # use NotificationChannelOptions.AVAILABLE_FOR_USE instead.
    supported_backends = list(BUILT_IN_BACKENDS)

    for backend_id, _ in get_messaging_backends():
        supported_backends.append(backend_id)

    channels_enum = models.IntegerChoices("NotificationChannel", supported_backends, start=0)
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
    def get_or_create_for_user(self, user: User, important: bool) -> "QuerySet[UserNotificationPolicy]":
        with transaction.atomic():
            User.objects.select_for_update().get(pk=user.pk)
            return self._get_or_create_for_user(user, important)

    def _get_or_create_for_user(self, user: User, important: bool) -> "QuerySet[UserNotificationPolicy]":
        notification_policies = super().filter(user=user, important=important)

        if notification_policies.exists():
            return notification_policies

        old_state = user.repr_settings_for_client_side_logging
        if important:
            policies = self.create_important_policies_for_user(user)
        else:
            policies = self.create_default_policies_for_user(user)

        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            user.organization,
            None,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )
        return policies

    def create_default_policies_for_user(self, user: User) -> "QuerySet[UserNotificationPolicy]":
        model = self.model

        policies_to_create = (
            model(
                user=user,
                step=model.Step.NOTIFY,
                notify_by=NotificationChannelOptions.DEFAULT_NOTIFICATION_CHANNEL,
                order=0,
            ),
            model(user=user, step=model.Step.WAIT, wait_delay=timezone.timedelta(minutes=15), order=1),
            model(user=user, step=model.Step.NOTIFY, notify_by=model.NotificationChannel.PHONE_CALL, order=2),
        )

        super().bulk_create(policies_to_create)
        return user.notification_policies.filter(important=False)

    def create_important_policies_for_user(self, user: User) -> "QuerySet[UserNotificationPolicy]":
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

        super().bulk_create(policies_to_create)
        return user.notification_policies.filter(important=True)


class UserNotificationPolicy(OrderedModel):
    objects = UserNotificationPolicyQuerySet.as_manager()
    order_with_respect_to = ("user", "important")

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

    ONE_MINUTE = timezone.timedelta(minutes=1)
    FIVE_MINUTES = timezone.timedelta(minutes=5)
    FIFTEEN_MINUTES = timezone.timedelta(minutes=15)
    THIRTY_MINUTES = timezone.timedelta(minutes=30)
    HOUR = timezone.timedelta(minutes=60)

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

    def __str__(self):
        return f"{self.pk}: {self.short_verbal}"

    @classmethod
    def get_short_verbals_for_user(cls, user: User) -> Tuple[Tuple[str], Tuple[str]]:
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
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_GENERAL,
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_CRITICAL,
    ] + [
        getattr(UserNotificationPolicy.NotificationChannel, backend_id)
        for backend_id, b in get_messaging_backends()
        if b.available_for_use
    ]

    DEFAULT_NOTIFICATION_CHANNEL = UserNotificationPolicy.NotificationChannel.SLACK

    SLACK_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [UserNotificationPolicy.NotificationChannel.SLACK]
    TELEGRAM_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [UserNotificationPolicy.NotificationChannel.TELEGRAM]
    EMAIL_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [UserNotificationPolicy.NotificationChannel.EMAIL]
    MOBILE_APP_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS = [
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_GENERAL,
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_CRITICAL,
    ]


class NotificationChannelAPIOptions(NotificationChannelOptions):
    LABELS = {
        UserNotificationPolicy.NotificationChannel.SLACK: "Slack mentions",
        UserNotificationPolicy.NotificationChannel.SMS: "SMS \U00002709\U0001F4F2",
        UserNotificationPolicy.NotificationChannel.PHONE_CALL: "Phone call \U0000260E",
        UserNotificationPolicy.NotificationChannel.TELEGRAM: "Telegram \U0001F916",
        UserNotificationPolicy.NotificationChannel.EMAIL: "Email \U0001F4E8",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_GENERAL: "Mobile App",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_CRITICAL: "Mobile App Critical",
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
        UserNotificationPolicy.NotificationChannel.EMAIL: "Email",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_GENERAL: "Mobile App",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_CRITICAL: "Mobile App Critical",
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
        UserNotificationPolicy.NotificationChannel.EMAIL: "notify_by_email",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_GENERAL: "notify_by_mobile_app",
        UserNotificationPolicy.NotificationChannel.MOBILE_PUSH_CRITICAL: "notify_by_mobile_app_critical",
    }
    LABELS.update(
        {
            getattr(UserNotificationPolicy.NotificationChannel, backend_id): "notify_by_{}".format(b.backend_id.lower())
            for backend_id, b in get_messaging_backends()
        }
    )
