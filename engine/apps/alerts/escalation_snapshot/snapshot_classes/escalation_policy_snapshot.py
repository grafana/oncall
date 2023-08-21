import datetime
import typing
from collections import namedtuple

from celery import Task
from django.db import transaction
from django.utils import timezone

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.alerts.escalation_snapshot.utils import eta_for_escalation_step_notify_if_time
from apps.alerts.models.alert_group_log_record import AlertGroupLogRecord
from apps.alerts.models.escalation_policy import EscalationPolicy
from apps.alerts.tasks import (
    custom_button_result,
    custom_webhook_result,
    notify_all_task,
    notify_group_task,
    notify_user_task,
    resolve_by_last_step_task,
)
from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.user_management.models import User

if typing.TYPE_CHECKING:
    from apps.alerts.models.alert_group import AlertGroup


class EscalationPolicySnapshot:
    __slots__ = (
        "id",
        "order",
        "step",
        "wait_delay",
        "notify_to_users_queue",
        "last_notified_user",
        "from_time",
        "to_time",
        "num_alerts_in_window",
        "num_minutes_in_window",
        "custom_button_trigger",
        "custom_webhook",
        "notify_schedule",
        "notify_to_group",
        "escalation_counter",
        "passed_last_time",
        "pause_escalation",
    )

    StepExecutionResultData = namedtuple(
        "StepExecutionResultData",
        ["eta", "stop_escalation", "start_from_beginning", "pause_escalation"],
    )

    StepExecutionFunc = typing.Callable[["AlertGroup", str], typing.Optional[StepExecutionResultData]]

    def __init__(
        self,
        id,
        order,
        step,
        wait_delay,
        notify_to_users_queue,
        last_notified_user,
        from_time,
        to_time,
        num_alerts_in_window,
        num_minutes_in_window,
        custom_button_trigger,
        custom_webhook,
        notify_schedule,
        notify_to_group,
        escalation_counter,
        passed_last_time,
        pause_escalation,
    ):
        self.id = id
        self.order = order
        self.step = step
        self.wait_delay = wait_delay
        self.notify_to_users_queue = notify_to_users_queue
        self.last_notified_user = last_notified_user
        self.from_time = from_time
        self.to_time = to_time
        self.num_alerts_in_window = num_alerts_in_window
        self.num_minutes_in_window = num_minutes_in_window
        self.custom_button_trigger = custom_button_trigger
        self.custom_webhook = custom_webhook
        self.notify_schedule = notify_schedule
        self.notify_to_group = notify_to_group
        self.escalation_counter = escalation_counter  # used for STEP_REPEAT_ESCALATION_N_TIMES
        self.passed_last_time = passed_last_time  # used for building escalation plan
        self.pause_escalation = pause_escalation  # used for STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW

    def __str__(self) -> str:
        return f"Escalation link, order: {self.order}, step: '{self.step_display}'"

    @property
    def step_display(self) -> str:
        return EscalationPolicy.STEP_CHOICES[self.step][1]

    @property
    def escalation_policy(self) -> typing.Optional[EscalationPolicy]:
        return EscalationPolicy.objects.filter(pk=self.id).first()

    @property
    def sorted_users_queue(self) -> typing.List[User]:
        return sorted(self.notify_to_users_queue, key=lambda user: (user.username or "", user.pk))

    @property
    def next_user_in_sorted_queue(self) -> User:
        users_queue = self.sorted_users_queue
        try:
            last_user_index = users_queue.index(self.last_notified_user)
        except ValueError:
            last_user_index = -1
        next_user = users_queue[(last_user_index + 1) % len(users_queue)]
        return next_user

    def execute(self, alert_group: "AlertGroup", reason) -> StepExecutionResultData:
        action_map: typing.Dict[typing.Optional[int], EscalationPolicySnapshot.StepExecutionFunc] = {
            EscalationPolicy.STEP_WAIT: self._escalation_step_wait,
            EscalationPolicy.STEP_FINAL_NOTIFYALL: self._escalation_step_notify_all,
            EscalationPolicy.STEP_REPEAT_ESCALATION_N_TIMES: self._escalation_step_repeat_escalation_n_times,
            EscalationPolicy.STEP_FINAL_RESOLVE: self._escalation_step_resolve,
            EscalationPolicy.STEP_NOTIFY_GROUP: self._escalation_step_notify_user_group,
            EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT: self._escalation_step_notify_user_group,
            EscalationPolicy.STEP_NOTIFY_SCHEDULE: self._escalation_step_notify_on_call_schedule,
            EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT: self._escalation_step_notify_on_call_schedule,
            EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON: self._escalation_step_trigger_custom_button,
            EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK: self._escalation_step_trigger_custom_webhook,
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE: self._escalation_step_notify_users_queue,
            EscalationPolicy.STEP_NOTIFY_IF_TIME: self._escalation_step_notify_if_time,
            EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW: self._escalation_step_notify_if_num_alerts_in_time_window,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS: self._escalation_step_notify_multiple_users,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT: self._escalation_step_notify_multiple_users,
            None: self._escalation_step_not_configured,
        }
        result = action_map[self.step](alert_group, reason)
        self.passed_last_time = timezone.now()  # used for building escalation plan
        # if step doesn't have data to return, return default values
        return result if result is not None else self._get_result_tuple()

    def _escalation_step_wait(self, alert_group: "AlertGroup", _reason: str) -> StepExecutionResultData:
        if self.wait_delay is not None:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                alert_group=alert_group,
                reason="wait",
                escalation_policy=self.escalation_policy,
                escalation_policy_step=self.step,
            )
        else:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                reason="wait",
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_WAIT_STEP_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
        wait_delay = self.wait_delay or EscalationPolicy.DEFAULT_WAIT_DELAY
        eta = timezone.now() + wait_delay
        log_record.save()
        return self._get_result_tuple(eta=eta)

    def _escalation_step_notify_all(self, alert_group: "AlertGroup", _reason: str) -> None:
        tasks = []
        notify_all = notify_all_task.signature(
            args=(alert_group.pk,),
            kwargs={"escalation_policy_snapshot_order": self.order},
            immutable=True,
        )
        tasks.append(notify_all)
        self._execute_tasks(tasks)

    def _escalation_step_notify_users_queue(self, alert_group: "AlertGroup", reason: str) -> None:
        tasks = []
        escalation_policy = self.escalation_policy
        if len(self.notify_to_users_queue) > 0:
            next_user = self.next_user_in_sorted_queue
            self.last_notified_user = next_user
            if escalation_policy is not None:
                escalation_policy.last_notified_user = next_user
                escalation_policy.save(update_fields=["last_notified_user"])

            notify_task = notify_user_task.signature(
                (
                    next_user.pk,
                    alert_group.pk,
                ),
                {
                    "reason": reason,
                },
                immutable=True,
            )

            tasks.append(notify_task)
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                author_id=next_user.pk,
                alert_group=alert_group,
                reason=reason,
                escalation_policy=escalation_policy,
                escalation_policy_step=self.step,
            )
        else:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_QUEUE_NO_RECIPIENTS,
                escalation_policy_step=self.step,
            )
        log_record.save()
        self._execute_tasks(tasks)

    def _escalation_step_notify_multiple_users(self, alert_group: "AlertGroup", reason: str) -> None:
        tasks = []
        escalation_policy = self.escalation_policy
        if len(self.notify_to_users_queue) > 0:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                alert_group=alert_group,
                reason=reason,
                escalation_policy=escalation_policy,
                escalation_policy_step=self.step,
            )

            for user in self.notify_to_users_queue:
                notify_task = notify_user_task.signature(
                    (
                        user.pk,
                        alert_group.pk,
                    ),
                    {
                        "reason": reason,
                        "important": self.step == EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
                    },
                    immutable=True,
                )

                tasks.append(notify_task)

                AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                    author=user,
                    alert_group=alert_group,
                    reason=reason,
                    escalation_policy=escalation_policy,
                    escalation_policy_step=self.step,
                ).save()
        else:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_MULTIPLE_NO_RECIPIENTS,
                escalation_policy_step=self.step,
            )
        log_record.save()
        self._execute_tasks(tasks)

    def _escalation_step_notify_on_call_schedule(self, alert_group: "AlertGroup", reason: str) -> None:
        tasks = []
        escalation_policy = self.escalation_policy
        on_call_schedule = self.notify_schedule
        self.notify_to_users_queue = []

        if on_call_schedule is None:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_SCHEDULE_DOES_NOT_SELECTED,
                escalation_policy_step=self.step,
            )
        else:
            notify_to_users_list = list_users_to_notify_from_ical(on_call_schedule)
            if notify_to_users_list is None:
                log_record = AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                    alert_group=alert_group,
                    escalation_policy=escalation_policy,
                    escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_ICAL_IMPORT_FAILED,
                    escalation_policy_step=self.step,
                    step_specific_info={"schedule_name": on_call_schedule.name},
                )
            elif len(notify_to_users_list) == 0:
                log_record = AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                    alert_group=alert_group,
                    reason=reason,
                    escalation_policy=escalation_policy,
                    escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_ICAL_NO_VALID_USERS,
                    escalation_policy_step=self.step,
                    step_specific_info={"schedule_name": on_call_schedule.name},
                )
            else:
                log_record = AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                    alert_group=alert_group,
                    reason=reason,
                    escalation_policy=escalation_policy,
                    escalation_policy_step=self.step,
                    step_specific_info={"schedule_name": on_call_schedule.name},
                )
                self.notify_to_users_queue = notify_to_users_list

                for notify_to_user in notify_to_users_list:
                    reason = "user is on duty by schedule ({}) defined in iCal".format(on_call_schedule.name)
                    notify_task = notify_user_task.signature(
                        (
                            notify_to_user.pk,
                            alert_group.pk,
                        ),
                        {
                            "reason": reason,
                            "important": self.step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
                        },
                        immutable=True,
                    )

                    tasks.append(notify_task)

                    AlertGroupLogRecord(
                        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                        author=notify_to_user,
                        alert_group=alert_group,
                        reason=reason,
                        escalation_policy=escalation_policy,
                        escalation_policy_step=self.step,
                    ).save()
        log_record.save()
        self._execute_tasks(tasks)

    def _escalation_step_notify_user_group(self, alert_group: "AlertGroup", reason: str) -> None:
        tasks = []
        self.notify_to_users_queue = []

        if self.notify_to_group is None:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                reason=reason,
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_GROUP_STEP_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
            log_record.save()
        else:
            notify_group = notify_group_task.signature(
                args=(alert_group.pk,),
                kwargs={
                    "escalation_policy_snapshot_order": self.order,
                },
                immutable=True,
            )
            tasks.append(notify_group)
        self._execute_tasks(tasks)

    def _escalation_step_notify_if_time(self, alert_group: "AlertGroup", _reason: str) -> StepExecutionResultData:
        eta = None

        if self.from_time is None or self.to_time is None:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IF_TIME_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
        else:
            eta = eta_for_escalation_step_notify_if_time(self.from_time, self.to_time)
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                author=None,
                alert_group=alert_group,
                reason="notify if time",
                eta=eta,
                escalation_policy=self.escalation_policy,
                escalation_policy_step=self.step,
            )

        log_record.save()
        return self._get_result_tuple(eta=eta)

    def _escalation_step_notify_if_num_alerts_in_time_window(
        self, alert_group: "AlertGroup", _reason: str
    ) -> typing.Optional[StepExecutionResultData]:
        # check if current escalation policy is configured properly, otherwise create an error log
        if self.num_alerts_in_window is None or self.num_minutes_in_window is None:
            AlertGroupLogRecord.objects.create(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IF_NUM_ALERTS_IN_WINDOW_STEP_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
            return None

        # create a log record only when escalation is paused for the first time
        if not self.pause_escalation:
            AlertGroupLogRecord.objects.create(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                author=None,
                alert_group=alert_group,
                reason="continue escalation if >X alerts per Y minutes",
                escalation_policy=self.escalation_policy,
                escalation_policy_step=self.step,
            )

        last_alert = alert_group.alerts.last()

        time_delta = datetime.timedelta(minutes=self.escalation_policy.num_minutes_in_window)
        num_alerts_in_window = alert_group.alerts.filter(created_at__gte=last_alert.created_at - time_delta).count()

        # pause escalation if there are not enough alerts in time window
        if num_alerts_in_window <= self.escalation_policy.num_alerts_in_window:
            self.pause_escalation = True
            return self._get_result_tuple(pause_escalation=True)
        return None

    def _escalation_step_trigger_custom_button(self, alert_group: "AlertGroup", _reason: str) -> None:
        tasks = []
        custom_button = self.custom_button_trigger
        if custom_button is not None:
            custom_button_task = custom_button_result.signature(
                (custom_button.pk, alert_group.pk),
                {
                    "escalation_policy_pk": self.id,
                },
                immutable=True,
            )
            tasks.append(custom_button_task)
        else:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_BUTTON_STEP_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
            log_record.save()
        self._execute_tasks(tasks)

    def _escalation_step_trigger_custom_webhook(self, alert_group: "AlertGroup", _reason: str) -> None:
        tasks = []
        webhook = self.custom_webhook
        if webhook is not None:
            custom_webhook_task = custom_webhook_result.signature(
                (webhook.pk, alert_group.pk),
                {
                    "escalation_policy_pk": self.id,
                },
                immutable=True,
            )
            tasks.append(custom_webhook_task)
        else:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=self.escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_BUTTON_STEP_IS_NOT_CONFIGURED,
                escalation_policy_step=self.step,
            )
            log_record.save()
        self._execute_tasks(tasks)

    def _escalation_step_repeat_escalation_n_times(
        self, alert_group: "AlertGroup", _reason: str
    ) -> typing.Optional[StepExecutionResultData]:
        if self.escalation_counter < EscalationPolicy.MAX_TIMES_REPEAT:
            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                author=None,
                alert_group=alert_group,
                reason="repeat escalation",
                escalation_policy=self.escalation_policy,
                escalation_policy_step=self.step,
            )
            log_record.save()
            self.escalation_counter += 1
            return self._get_result_tuple(start_from_beginning=True)
        return None

    def _escalation_step_resolve(self, alert_group: "AlertGroup", _reason: str) -> StepExecutionResultData:
        tasks = []
        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
            author=None,
            alert_group=alert_group,
            reason="final resolve",
            escalation_policy=self.escalation_policy,
            escalation_policy_step=self.step,
        )
        log_record.save()
        resolve_by_last_step = resolve_by_last_step_task.signature((alert_group.pk,), immutable=True)
        tasks.append(resolve_by_last_step)
        self._execute_tasks(tasks)
        return self._get_result_tuple(stop_escalation=True)

    def _escalation_step_not_configured(self, alert_group: "AlertGroup", _reason: str) -> None:
        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
            alert_group=alert_group,
            escalation_policy=self.escalation_policy,
            escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_UNSPECIFIED_STEP,
        )
        log_record.save()

    def _execute_tasks(self, tasks: typing.List[Task]) -> None:
        def _apply_tasks() -> None:
            for task in tasks:
                task.apply_async()

        transaction.on_commit(_apply_tasks)

    def _get_result_tuple(
        self, eta=None, stop_escalation=False, start_from_beginning=False, pause_escalation=False
    ) -> StepExecutionResultData:
        # use default delay for eta, if eta was not counted by step
        eta = eta or timezone.now() + datetime.timedelta(seconds=NEXT_ESCALATION_DELAY)
        return self.StepExecutionResultData(eta, stop_escalation, start_from_beginning, pause_escalation)
