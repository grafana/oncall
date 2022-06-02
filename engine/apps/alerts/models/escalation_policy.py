from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from ordered_model.models import OrderedModel

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_escalation_policy():
    prefix = "E"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while EscalationPolicy.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="EscalationPolicy"
        )
        failure_counter += 1

    return new_public_primary_key


class EscalationPolicy(OrderedModel):

    order_with_respect_to = "escalation_chain"

    MAX_TIMES_REPEAT = 5

    (
        STEP_WAIT,
        STEP_NOTIFY,
        STEP_FINAL_NOTIFYALL,
        STEP_REPEAT_ESCALATION_N_TIMES,
        STEP_FINAL_RESOLVE,
        STEP_NOTIFY_GROUP,
        STEP_NOTIFY_SCHEDULE,
        STEP_NOTIFY_IMPORTANT,
        STEP_NOTIFY_GROUP_IMPORTANT,
        STEP_NOTIFY_SCHEDULE_IMPORTANT,
        STEP_TRIGGER_CUSTOM_BUTTON,
        STEP_NOTIFY_USERS_QUEUE,
        STEP_NOTIFY_IF_TIME,
        STEP_NOTIFY_MULTIPLE_USERS,
        STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
    ) = range(16)

    # Must be the same order as previous
    STEP_CHOICES = (
        (STEP_WAIT, "Wait"),
        (STEP_NOTIFY, "Notify User"),
        (STEP_FINAL_NOTIFYALL, "Notify Whole Channel"),
        (STEP_REPEAT_ESCALATION_N_TIMES, "Repeat Escalation (5 times max)"),
        (STEP_FINAL_RESOLVE, "Resolve"),
        (STEP_NOTIFY_GROUP, "Notify Group"),
        (STEP_NOTIFY_SCHEDULE, "Notify Schedule"),
        (STEP_NOTIFY_IMPORTANT, "Notify User (Important)"),
        (STEP_NOTIFY_GROUP_IMPORTANT, "Notify Group (Important)"),
        (STEP_NOTIFY_SCHEDULE_IMPORTANT, "Notify Schedule (Important)"),
        (STEP_TRIGGER_CUSTOM_BUTTON, "Trigger Outgoing Webhook"),
        (STEP_NOTIFY_USERS_QUEUE, "Notify User (next each time)"),
        (STEP_NOTIFY_IF_TIME, "Continue escalation only if time is from"),
        (STEP_NOTIFY_MULTIPLE_USERS, "Notify multiple Users"),
        (STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT, "Notify multiple Users (Important)"),
        (STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW, "Continue escalation if >X alerts per Y minutes"),
    )

    # Ordered step choices available for internal api.
    # There are not important steps because they are presented as default step with important flag
    INTERNAL_API_STEPS = [
        # Common
        STEP_WAIT,
        STEP_NOTIFY_MULTIPLE_USERS,
        STEP_NOTIFY_SCHEDULE,
        STEP_FINAL_RESOLVE,
        # Slack
        STEP_FINAL_NOTIFYALL,
        STEP_NOTIFY_GROUP,
        # Other
        STEP_TRIGGER_CUSTOM_BUTTON,
        STEP_NOTIFY_USERS_QUEUE,
        STEP_NOTIFY_IF_TIME,
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
        STEP_REPEAT_ESCALATION_N_TIMES,
    ]
    # Steps can be stored in db while interacting with internal api
    # Includes important versions of default steps
    INTERNAL_DB_STEPS = [
        STEP_WAIT,
        STEP_FINAL_NOTIFYALL,
        STEP_FINAL_RESOLVE,
        STEP_NOTIFY_GROUP,
        STEP_NOTIFY_SCHEDULE,
        STEP_NOTIFY_GROUP_IMPORTANT,
        STEP_NOTIFY_SCHEDULE_IMPORTANT,
        STEP_NOTIFY_USERS_QUEUE,
        STEP_NOTIFY_IF_TIME,
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
        STEP_NOTIFY_MULTIPLE_USERS,
        STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
        STEP_TRIGGER_CUSTOM_BUTTON,
        STEP_REPEAT_ESCALATION_N_TIMES,
    ]

    # Maps internal api's steps choices to their verbal. First string in tuple is display name for existent step.
    # Second one is for option in dropdown.
    INTERNAL_API_STEPS_TO_VERBAL_MAP = {
        # Common steps
        STEP_WAIT: ("Wait {{wait_delay}} minute(s)", "Wait"),
        STEP_NOTIFY_MULTIPLE_USERS: ("Start {{importance}} notification for {{users}}", "Notify users"),
        STEP_NOTIFY_SCHEDULE: (
            "Start {{importance}} notification for schedule {{schedule}}",
            "Notify users from on-call schedule",
        ),
        STEP_FINAL_RESOLVE: ("Resolve incident automatically", "Resolve incident automatically"),
        # Slack
        STEP_FINAL_NOTIFYALL: ("Notify whole Slack channel", "Notify whole Slack channel"),
        STEP_NOTIFY_GROUP: (
            "Start {{importance}} notification for everyone from Slack User Group {{slack_user_group}}",
            "Notify Slack User Group",
        ),
        # Other
        STEP_TRIGGER_CUSTOM_BUTTON: ("Trigger outgoing webhook {{custom_action}}", "Trigger outgoing webhook"),
        STEP_NOTIFY_USERS_QUEUE: ("Round robin notification for {{users}}", "Notify users one by one (round-robin)"),
        STEP_NOTIFY_IF_TIME: (
            "Continue escalation if current time is in {{timerange}} ",
            "Continue escalation if current time is in range",
        ),
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW: (
            "Continue escalation if >{{num_alerts_in_window}} alerts per {{num_minutes_in_window}} minutes",
            "Continue escalation if >X alerts per Y minutes",
        ),
        STEP_REPEAT_ESCALATION_N_TIMES: (
            "Repeat escalation from the beginning (5 times max)",
            "Repeat escalations from the beginning (5 times max)",
        ),
    }

    STEPS_WITH_NO_IMPORTANT_VERSION_SET = {
        STEP_WAIT,
        STEP_FINAL_NOTIFYALL,
        STEP_FINAL_RESOLVE,
        STEP_TRIGGER_CUSTOM_BUTTON,
        STEP_NOTIFY_USERS_QUEUE,
        STEP_NOTIFY_IF_TIME,
        STEP_REPEAT_ESCALATION_N_TIMES,
    }

    DEFAULT_TO_IMPORTANT_STEP_MAPPING = {
        STEP_NOTIFY_GROUP: STEP_NOTIFY_GROUP_IMPORTANT,
        STEP_NOTIFY_SCHEDULE: STEP_NOTIFY_SCHEDULE_IMPORTANT,
        STEP_NOTIFY_MULTIPLE_USERS: STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
    }
    IMPORTANT_TO_DEFAULT_STEP_MAPPING = {
        STEP_NOTIFY_GROUP_IMPORTANT: STEP_NOTIFY_GROUP,
        STEP_NOTIFY_SCHEDULE_IMPORTANT: STEP_NOTIFY_SCHEDULE,
        STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT: STEP_NOTIFY_MULTIPLE_USERS,
    }

    # Default steps are just usual version of important steps. E.g. notify group - notify group important
    DEFAULT_STEPS_SET = {
        STEP_NOTIFY_GROUP,
        STEP_NOTIFY_SCHEDULE,
        STEP_NOTIFY_MULTIPLE_USERS,
    }

    IMPORTANT_STEPS_SET = {
        STEP_NOTIFY_GROUP_IMPORTANT,
        STEP_NOTIFY_SCHEDULE_IMPORTANT,
        STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
    }

    SLACK_INTEGRATION_REQUIRED_STEPS = [
        STEP_NOTIFY_GROUP,
        STEP_NOTIFY_GROUP_IMPORTANT,
        STEP_FINAL_NOTIFYALL,
    ]

    PUBLIC_STEP_CHOICES = [
        STEP_WAIT,
        STEP_NOTIFY_SCHEDULE,
        STEP_NOTIFY_MULTIPLE_USERS,
        STEP_NOTIFY_USERS_QUEUE,
        STEP_NOTIFY_GROUP,
        STEP_FINAL_RESOLVE,
        STEP_FINAL_NOTIFYALL,
        STEP_TRIGGER_CUSTOM_BUTTON,
        STEP_NOTIFY_IF_TIME,
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
        STEP_REPEAT_ESCALATION_N_TIMES,
    ]

    PUBLIC_STEP_CHOICES_MAP = {
        STEP_WAIT: "wait",
        STEP_NOTIFY: "notify_one_person",
        STEP_FINAL_NOTIFYALL: "notify_whole_channel",
        STEP_FINAL_RESOLVE: "resolve",
        STEP_NOTIFY_GROUP: "notify_user_group",
        STEP_NOTIFY_GROUP_IMPORTANT: "notify_user_group",
        STEP_NOTIFY_IMPORTANT: "notify_one_person",
        STEP_NOTIFY_SCHEDULE: "notify_on_call_from_schedule",
        STEP_NOTIFY_SCHEDULE_IMPORTANT: "notify_on_call_from_schedule",
        STEP_TRIGGER_CUSTOM_BUTTON: "trigger_action",
        STEP_NOTIFY_USERS_QUEUE: "notify_person_next_each_time",
        STEP_NOTIFY_MULTIPLE_USERS: "notify_persons",
        STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT: "notify_persons",
        STEP_NOTIFY_IF_TIME: "notify_if_time_from_to",
        STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW: "notify_if_num_alerts_in_window",
        STEP_REPEAT_ESCALATION_N_TIMES: "repeat_escalation",
    }

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_escalation_policy,
    )

    escalation_chain = models.ForeignKey(
        "alerts.EscalationChain", on_delete=models.CASCADE, related_name="escalation_policies"
    )

    notify_to_users_queue = models.ManyToManyField("user_management.User")

    last_notified_user = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        related_name="last_notified_in_escalation_policies",
        default=None,
        null=True,
    )

    step = models.IntegerField(choices=STEP_CHOICES, default=None, null=True)

    notify_to_group = models.ForeignKey(
        "slack.SlackUserGroup",
        on_delete=models.SET_NULL,
        default=None,
        null=True,
    )

    notify_schedule = models.ForeignKey(
        "schedules.OnCallSchedule",
        on_delete=models.SET_NULL,
        related_name="escalation_policies",
        null=True,
        default=None,
    )

    custom_button_trigger = models.ForeignKey(
        "alerts.CustomButton",
        on_delete=models.CASCADE,
        related_name="escalation_policies",
        default=None,
        null=True,
    )

    ONE_MINUTE = timezone.timedelta(minutes=1)
    FIVE_MINUTES = timezone.timedelta(minutes=5)
    FIFTEEN_MINUTES = timezone.timedelta(minutes=15)
    THIRTY_MINUTES = timezone.timedelta(minutes=30)
    HOUR = timezone.timedelta(minutes=60)

    DEFAULT_WAIT_DELAY = timezone.timedelta(minutes=5)

    DURATION_CHOICES = (
        (ONE_MINUTE, "1 min"),
        (FIVE_MINUTES, "5 min"),
        (FIFTEEN_MINUTES, "15 min"),
        (THIRTY_MINUTES, "30 min"),
        (HOUR, "60 min"),
    )

    WEB_DURATION_CHOICES = (
        (ONE_MINUTE, "1"),
        (FIVE_MINUTES, "5"),
        (FIFTEEN_MINUTES, "15"),
        (THIRTY_MINUTES, "30"),
        (HOUR, "60"),
    )

    # the same choices for web, but in integer format for minutes instead of timedelta
    WEB_DURATION_CHOICES_MINUTES = [(choice[0].seconds // 60, choice[1]) for choice in WEB_DURATION_CHOICES]

    wait_delay = models.DurationField(default=None, null=True, choices=DURATION_CHOICES)

    from_time = models.TimeField(null=True, default=None)
    to_time = models.TimeField(null=True, default=None)

    # fields needed for escalation step "Continue escalation if >X alerts per Y minutes"
    num_alerts_in_window = models.PositiveIntegerField(null=True, default=None)
    num_minutes_in_window = models.PositiveIntegerField(null=True, default=None)

    def __str__(self):
        return f"{self.pk}: {self.step_type_verbal}"

    @property
    def step_type_verbal(self):
        return self.STEP_CHOICES[self.step][1] if self.step is not None else "Empty"

    @property
    def repr_settings_for_client_side_logging(self):
        """
        Example of execution:
            step: 'Notify multiple Users', order: 0, important: No, users: Alex, Bob
        Another example:
            step: 'Continue escalation only if time is from', order: 4, from time: 09:40:00 (UTC), to time: 15:40:00 (UTC)
        """
        result = f"step: '{self.step_type_verbal}', order: {self.order}"
        if self.step not in EscalationPolicy.STEPS_WITH_NO_IMPORTANT_VERSION_SET:
            result += f", important: {'Yes' if self.step in EscalationPolicy.IMPORTANT_STEPS_SET else 'No'}"
        if self.step == EscalationPolicy.STEP_WAIT:
            result += f", wait: {self.get_wait_delay_display() if self.wait_delay else 'default'}"
        elif self.step in [EscalationPolicy.STEP_NOTIFY_GROUP, EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT]:
            result += f", user group: {self.notify_to_group.name if self.notify_to_group else 'not selected'}"
        elif self.step in [EscalationPolicy.STEP_NOTIFY_SCHEDULE, EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT]:
            result += f", on-call schedule: {self.notify_schedule.name if self.notify_schedule else 'not selected'}"
        elif self.step == EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
            result += f", action: {self.custom_button_trigger.name if self.custom_button_trigger else 'not selected'}"
        elif self.step in [
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
        ]:
            if self.notify_to_users_queue:
                users_verbal = ", ".join([user.username for user in self.sorted_users_queue])
            else:
                users_verbal = "not selected"
            result += f", users: {users_verbal}"
        elif self.step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
            if self.from_time:
                from_time_verbal = self.from_time.isoformat() + " (UTC)"
            else:
                from_time_verbal = "not selected"
            if self.to_time:
                to_time_verbal = self.to_time.isoformat() + " (UTC)"
            else:
                to_time_verbal = "not selected"
            result += f", from time: {from_time_verbal}, to time: {to_time_verbal}"
        return result

    @property
    def sorted_users_queue(self):
        return sorted(self.notify_to_users_queue.all(), key=lambda user: (user.username or "", user.pk))

    @property
    def slack_integration_required(self):
        if self.step in self.SLACK_INTEGRATION_REQUIRED_STEPS:
            return True
        else:
            return False

    @staticmethod
    def get_step_display_name(step):
        step_name = ""
        for step_choice in EscalationPolicy.STEP_CHOICES:
            if step_choice[0] == step:
                step_name = step_choice[1]
                break
        return step_name
