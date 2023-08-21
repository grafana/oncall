import typing

from django.db.models import Q
from django.utils import timezone

from apps.base.messaging import get_messaging_backend_from_id
from apps.schedules.ical_utils import list_users_to_notify_from_ical

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, AlertGroupLogRecord, ResolutionNote
    from apps.base.models import UserNotificationPolicyLogRecord


class IncidentLogBuilder:
    def __init__(self, alert_group: "AlertGroup"):
        self.alert_group = alert_group

    def get_log_records_list(
        self, with_resolution_notes: bool = False
    ) -> typing.List[typing.Union["AlertGroupLogRecord", "ResolutionNote", "UserNotificationPolicyLogRecord"]]:
        """
        Generates list of `AlertGroupLogRecord` and `UserNotificationPolicyLogRecord` logs.

        `ResolutionNote`s are optionally included if `with_resolution_notes` is `True`.
        """
        all_log_records: typing.List[
            typing.Union["AlertGroupLogRecord", "ResolutionNote", "UserNotificationPolicyLogRecord"]
        ] = list()
        # get logs from AlertGroupLogRecord
        alert_group_log_records = self._get_log_records_for_after_resolve_report()
        all_log_records.extend(alert_group_log_records)

        # get logs from UserNotificationPolicyLogRecord
        user_notification_log_records = self._get_user_notification_log_records_for_log_report()
        all_log_records.extend(user_notification_log_records)

        if with_resolution_notes:
            resolution_notes = self._get_resolution_notes()
            all_log_records.extend(resolution_notes)
        # sort logs by date
        all_log_records_sorted = sorted(all_log_records, key=lambda log: log.created_at)
        return all_log_records_sorted

    def _get_log_records_for_after_resolve_report(self) -> "RelatedManager['AlertGroupLogRecord']":
        from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy

        excluded_log_types = [
            AlertGroupLogRecord.TYPE_ESCALATION_FINISHED,
            AlertGroupLogRecord.TYPE_INVITATION_TRIGGERED,
            AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED,
            AlertGroupLogRecord.TYPE_WIPED,
            AlertGroupLogRecord.TYPE_DELETED,
        ]
        excluded_escalation_steps = [EscalationPolicy.STEP_WAIT, EscalationPolicy.STEP_FINAL_RESOLVE]
        not_excluded_steps_with_author = [
            EscalationPolicy.STEP_NOTIFY,
            EscalationPolicy.STEP_NOTIFY_IMPORTANT,
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
        ]

        # exclude logs that we don't want to see in after resolve report
        # exclude logs with deleted root or dependent alert group
        return (
            self.alert_group.log_records.exclude(
                Q(
                    Q(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED)
                    & Q(author__isnull=False)
                    & Q(
                        # new logs with saved escalation step
                        Q(
                            Q(escalation_policy_step__isnull=False)
                            & ~Q(escalation_policy_step__in=not_excluded_steps_with_author)
                        )
                        |
                        # old logs
                        Q(
                            Q(escalation_policy_step__isnull=True, escalation_policy__step__isnull=False)
                            & ~Q(escalation_policy__step__in=not_excluded_steps_with_author)
                        )
                    )
                )
                | Q(type__in=excluded_log_types)
                | Q(escalation_policy_step__in=excluded_escalation_steps)
                | Q(  # new logs with saved escalation step
                    escalation_policy_step__isnull=True, escalation_policy__step__in=excluded_escalation_steps
                )
                | Q(  # old logs
                    Q(Q(type=AlertGroupLogRecord.TYPE_ATTACHED) | Q(type=AlertGroupLogRecord.TYPE_UNATTACHED))
                    & Q(Q(root_alert_group__isnull=True) & Q(dependent_alert_group__isnull=True))
                )
            )
            .select_related("author")
            .distinct()
            .order_by("created_at")
        )

    def _get_user_notification_log_records_for_log_report(self) -> "RelatedManager['UserNotificationPolicyLogRecord']":
        from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

        # exclude user notification logs with step 'wait' or with status 'finished'
        return (
            self.alert_group.personal_log_records.exclude(
                Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FINISHED)
                | Q(
                    Q(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED)
                    & Q(notification_policy__step=UserNotificationPolicy.Step.WAIT)
                )
            )
            .select_related("author")
            .distinct()
            .order_by("created_at")
        )

    def _get_resolution_notes(self) -> "RelatedManager['ResolutionNote']":
        return self.alert_group.resolution_notes.select_related("author", "resolution_note_slack_message").order_by(
            "created_at"
        )

    def get_incident_escalation_plan(self, for_slack=False):
        """
        Generates dict with escalation plan with timedelta as keys and list with plan lines as values
        :param for_slack: (bool) add user slack id to plan line or not
        :return:
        """
        incident_escalation_plan = dict()
        incident_escalation_plan = self._add_invitation_plan(incident_escalation_plan, for_slack=for_slack)
        if not self.alert_group.acknowledged and not self.alert_group.is_silenced_forever:
            incident_escalation_plan = self._add_escalation_plan(incident_escalation_plan, for_slack=for_slack)
        final_incident_escalation_plan = self._finalize_escalation_plan_dict(incident_escalation_plan)
        return final_incident_escalation_plan

    def _add_escalation_plan(self, escalation_plan_dict, for_slack=False):
        """
        Returns plan for future escalations
        :param escalation_plan_dict:
        :param for_slack:
        :return: {timedelta: [{"user_id": user.pk, "plan_lines": [#rendered escalation policy line, ]}, ..., ...], ...}
        """
        esc_timedelta = timezone.timedelta(seconds=0)  # timedelta for next escalation step
        now = timezone.now()

        # check if escalation snapshot wasn't saved and channel filter was deleted.
        # We cannot generate escalation plan in this case
        escalation_snapshot = self.alert_group.escalation_snapshot
        if not self.alert_group.has_escalation_policies_snapshots:
            return escalation_plan_dict

        if self.alert_group.silenced_until:
            timedelta = self.alert_group.silenced_until - now
            esc_timedelta += timedelta

        # get starting point for escalation plan, we are not interested in previous escalation logs
        stop_escalation_log = self.alert_group.last_stop_escalation_log

        # set starting point to 0 if incident wasn't acknowledged or resolved
        stop_escalation_log_pk = stop_escalation_log.pk if stop_escalation_log else 0

        # render escalation plan from escalation_snapshot
        escalation_plan_dict = self._render_escalation_plan_from_escalation_snapshot(
            escalation_plan_dict,
            stop_escalation_log_pk,
            esc_timedelta,
            escalation_snapshot,
            for_slack,
        )
        return escalation_plan_dict

    def _render_escalation_plan_from_escalation_snapshot(
        self, escalation_plan_dict, stop_escalation_log_pk, esc_timedelta, escalation_snapshot, for_slack=False
    ):
        from apps.alerts.models import EscalationPolicy

        now = timezone.now()
        escalation_eta = None
        last_log_timedelta = None
        escalation_policies_snapshots = escalation_snapshot.escalation_policies_snapshots

        # get escalation log of the last passed escalation step
        last_escalation_log = (
            self.alert_group.log_records.filter(
                escalation_policy_step__isnull=False,
                pk__gt=stop_escalation_log_pk,
            )
            .order_by("pk")
            .last()
        )
        if last_escalation_log is not None:
            escalation_eta = last_escalation_log.eta
            last_log_timedelta = now - last_escalation_log.created_at

        # get order of next escalation step
        escalation_policy_order = escalation_snapshot.last_active_escalation_policy_order or 0
        # do not exclude wait step, because we need it to count timedelta
        if (
            escalation_policies_snapshots
            and escalation_policies_snapshots[escalation_policy_order].step != EscalationPolicy.STEP_WAIT
        ):
            escalation_policy_order += 1

        if len(escalation_policies_snapshots) > 0 and not escalation_eta:
            future_step_timedelta = None
            for escalation_policy_snapshot in escalation_policies_snapshots:
                step_timedelta = esc_timedelta
                future_step = escalation_policy_snapshot.order >= escalation_policy_order  # step not passed yet
                if future_step and escalation_policy_snapshot.step == EscalationPolicy.STEP_WAIT:
                    wait_delay = escalation_policy_snapshot.wait_delay or EscalationPolicy.DEFAULT_WAIT_DELAY
                    esc_timedelta += wait_delay  # increase timedelta for next steps
                    continue
                # get relative timedelta for step
                elif future_step and last_log_timedelta:
                    future_step_timedelta = esc_timedelta - last_log_timedelta
                elif not future_step:
                    passed_last_time = escalation_policy_snapshot.passed_last_time
                    if passed_last_time is not None:
                        step_timedelta = esc_timedelta - (now - passed_last_time)
                    else:
                        step_timedelta = esc_timedelta

                step_timedelta = future_step_timedelta or step_timedelta

                # stop plan generation if there is resolve step in escalation plan
                if future_step and escalation_policy_snapshot.step == EscalationPolicy.STEP_FINAL_RESOLVE:
                    escalation_plan_dict = IncidentLogBuilder._remove_future_plan(esc_timedelta, escalation_plan_dict)
                    escalation_step_plan_dict = self._render_escalation_step_plan_from_escalation_policy_snapshot(
                        escalation_policy_snapshot,
                        escalation_snapshot,
                        for_slack=for_slack,
                        future_step=future_step,
                        esc_timedelta=step_timedelta,
                    )
                    step_timedelta += timezone.timedelta(seconds=5)  # make this step the last in plan

                    for timedelta, plan in escalation_step_plan_dict.items():
                        timedelta += step_timedelta
                        escalation_plan_dict.setdefault(timedelta, []).extend(plan)
                    break

                # render escalation and notification plan lines for step
                escalation_step_plan_dict = self._render_escalation_step_plan_from_escalation_policy_snapshot(
                    escalation_policy_snapshot,
                    escalation_snapshot,
                    for_slack=for_slack,
                    future_step=future_step,
                    esc_timedelta=step_timedelta,
                )
                escalation_plan_dict = self._correct_users_notification_plan(
                    escalation_plan_dict, escalation_step_plan_dict, step_timedelta
                )
        return escalation_plan_dict

    @staticmethod
    def _remove_future_plan(timedelta_to_remove, plan_dict):
        """
        Removes plan with higher timedelta (for events, that will start later, than selected time
        (timedelta_to_remove)).
        :param timedelta_to_remove:
        :param plan_dict:
        :return: new plan dict
        """
        new_plan_dict = dict()
        for timedelta in sorted(plan_dict):
            if timedelta <= timedelta_to_remove:
                new_plan_dict[timedelta] = plan_dict[timedelta]
        return new_plan_dict

    def _add_invitation_plan(self, escalation_plan_dict, for_slack=False):
        """
        Adds notification plan for invitation
        :param escalation_plan_dict:
        :param for_slack:
        :return: {timedelta: [{"user_id": user.pk, "plan_lines": [#rendered escalation policy line, ]}, ..., ...], ...}
        """
        from apps.alerts.models import Invitation

        now = timezone.now()
        for invitation in self.alert_group.invitations.filter(is_active=True):
            invitation_timedelta = timezone.timedelta()
            current_attempt = invitation.attempt - 1
            # generate notification plan for each attempt
            for attempt in range(current_attempt, Invitation.ATTEMPTS_LIMIT + 1):
                notification_plan = self._get_notification_plan_for_user(
                    invitation.invitee,
                    for_slack=for_slack,
                    future_step=attempt >= invitation.attempt,
                )
                escalation_plan_dict = self._correct_users_notification_plan(
                    escalation_plan_dict, notification_plan, invitation_timedelta
                )
                started_timedelta = now - invitation.created_at
                invitation_timedelta += Invitation.get_delay_by_attempt(attempt) - started_timedelta
        return escalation_plan_dict

    def _correct_users_notification_plan(self, escalation_plan_dict, notification_plan_dict, esc_time):
        """
        Check if escalation_plan_dict has user notification events with higher timedelta
        than timedelta of current step. If it has, remove future notification events for users that
        repeatedly notified by current escalation step from current escalation_plan_dict
        because their notification chain will start from the beginning.

        :param escalation_plan_dict:
        :param notification_plan_dict:
        :param esc_time:
        :return:
        """

        future_step_timedelta = None

        later_events_exist = False
        for timedelta in escalation_plan_dict:
            if timedelta > esc_time:
                later_events_exist = True
                break
        if later_events_exist:
            earliest_events = notification_plan_dict.get(timezone.timedelta(), [])
            notification_plans_to_remove = []
            for event_dict in earliest_events:  # [{"user_id": user.pk, "plan_lines": []}, {"plan_lines": []}]
                user_id = event_dict.get("user_id")
                if user_id:
                    notification_plans_to_remove.append(user_id)
            new_escalation_policies_dict = {}

            for timedelta in sorted(escalation_plan_dict):
                # do not add step from escalation plan if its timedelta < 0
                if timedelta < timezone.timedelta():
                    continue
                events_list = list()
                for event_dict in escalation_plan_dict[timedelta]:
                    if event_dict.get("is_the_first_notification_step"):
                        if (
                            future_step_timedelta is None
                            and timedelta > esc_time
                            and event_dict.get("user_id") in notification_plans_to_remove
                        ):
                            future_step_timedelta = timedelta
                    if (
                        timedelta < esc_time
                        or event_dict.get("user_id") not in notification_plans_to_remove
                        or future_step_timedelta is not None
                    ):
                        events_list.append(event_dict)
                if len(events_list) > 0:
                    new_escalation_policies_dict.setdefault(timedelta, []).extend(events_list)

            escalation_plan_dict = new_escalation_policies_dict

        for timedelta, plan in notification_plan_dict.items():
            timedelta = esc_time + timedelta
            if future_step_timedelta is None or future_step_timedelta > timedelta:
                escalation_plan_dict.setdefault(timedelta, []).extend(plan)

        return escalation_plan_dict

    def _finalize_escalation_plan_dict(self, escalation_dict):
        """
        It changes escalation dict structure
        from {timedelta: [{"user_id": user.pk, "plan_lines": []}, {"plan_lines": []}]}
        to {timedelta: [all plan lines for this timedelta]}
        :param escalation_dict:
        :return:
        """
        final_escalation_dict = dict()
        for timedelta in escalation_dict:
            plan_lines_list = list()
            for event_dict in escalation_dict[timedelta]:
                plan_lines_list.extend(event_dict["plan_lines"])
            if len(plan_lines_list) > 0:
                timedelta = timedelta if timedelta > timezone.timedelta() else timezone.timedelta()
                final_escalation_dict.setdefault(timedelta, []).extend(plan_lines_list)
        return final_escalation_dict

    def _render_escalation_step_plan_from_escalation_policy_snapshot(
        self,
        escalation_policy_snapshot,
        escalation_snapshot,
        for_slack=False,
        future_step=False,
        esc_timedelta=None,
    ):
        """
        Renders escalation and notification policies plan dict.

        :param escalation_policy_snapshot:
        :param escalation_snapshot:
        :param for_slack: (bool) add or not user slack id to user notification plan line
        :param future_step: (bool) step not passed yet
        :param esc_timedelta: timedelta of escalation step

        :return: dict with timedelta as a key and list with escalation and notification plan lines as a value
        """
        from apps.alerts.models import EscalationPolicy

        escalation_plan_dict = {}
        timedelta = timezone.timedelta()
        if escalation_policy_snapshot.step in [
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
        ]:
            users_to_notify = escalation_policy_snapshot.sorted_users_queue
            if future_step:
                if users_to_notify:
                    plan_line = f'escalation step "{escalation_policy_snapshot.step_display}"'
                    if escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_USERS_QUEUE:
                        try:
                            last_user_index = users_to_notify.index(escalation_policy_snapshot.last_notified_user)
                        except ValueError:
                            last_user_index = -1
                        user_to_notify = users_to_notify[(last_user_index + 1) % len(users_to_notify)]
                        users_to_notify = [user_to_notify]
                else:
                    plan_line = (
                        f'escalation step "{escalation_policy_snapshot.step_display}" with no recipients. ' f"Skipping"
                    )
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
            elif escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_USERS_QUEUE:
                last_notified_user = escalation_policy_snapshot.last_notified_user
                users_to_notify = [last_notified_user] if last_notified_user else []

            for user_to_notify in users_to_notify:
                notification_plan_dict = self._get_notification_plan_for_user(
                    user_to_notify,
                    important=escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
                    for_slack=for_slack,
                    future_step=future_step,
                )
                # notification_plan_dict structure - {timedelta: [{"user_id": user.pk, "plan_lines": []}]
                for timedelta, notification_plan in notification_plan_dict.items():
                    escalation_plan_dict.setdefault(timedelta, []).extend(notification_plan)

        elif escalation_policy_snapshot.step == EscalationPolicy.STEP_FINAL_NOTIFYALL:
            channel_id = escalation_snapshot.slack_channel_id
            users_to_notify = []
            if future_step:
                if self.alert_group.is_presented_in_slack and channel_id:
                    plan_line = f'escalation step "{escalation_policy_snapshot.step_display}"'
                    slack_team_identity = self.alert_group.slack_message.slack_team_identity
                    users_to_notify = slack_team_identity.get_users_from_slack_conversation_for_organization(
                        channel_id=channel_id,
                        organization=self.alert_group.channel.organization,
                    )
                else:
                    plan_line = (
                        f'escalation step "{escalation_policy_snapshot.step_display}" is slack specific. ' f"Skipping"
                    )
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
            else:
                users_to_notify = escalation_policy_snapshot.notify_to_users_queue

            for user_to_notify in users_to_notify:
                notification_plan_dict = self._get_notification_plan_for_user(
                    user_to_notify,
                    important=escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_IMPORTANT,
                    for_slack=for_slack,
                    future_step=future_step,
                )
                # notification_plan_dict structure - {timedelta: [{"user_id": user.pk, "plan_lines": []}]
                for timedelta, notification_plan in notification_plan_dict.items():
                    escalation_plan_dict.setdefault(timedelta, []).extend(notification_plan)

        elif escalation_policy_snapshot.step == EscalationPolicy.STEP_FINAL_RESOLVE:
            if future_step:
                plan_line = "resolve automatically"
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
        elif escalation_policy_snapshot.step == EscalationPolicy.STEP_REPEAT_ESCALATION_N_TIMES:
            if future_step:
                escalation_counter = escalation_policy_snapshot.escalation_counter
                repeat_times = EscalationPolicy.MAX_TIMES_REPEAT - escalation_counter
                if repeat_times > 0:
                    plan_line = f"repeat escalation from the beginning ({repeat_times} times)"
                else:
                    plan_line = 'skip step "Repeat Escalation"'
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
        elif escalation_policy_snapshot.step in [
            EscalationPolicy.STEP_NOTIFY_GROUP,
            EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
        ]:
            users_to_notify = []
            if future_step:
                if self.alert_group.is_presented_in_slack:
                    user_group = escalation_policy_snapshot.notify_to_group
                    if user_group is not None:
                        users_to_notify = user_group.get_users_from_members_for_organization(
                            self.alert_group.channel.organization
                        )
                        user_group_handle = user_group.handle
                        important_text = ""
                        if escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT:
                            important_text = " (Important)"
                        plan_line = f'escalation step "Notify @{user_group_handle} User Group{important_text}"'
                    else:
                        plan_line = (
                            f'escalation step "{escalation_policy_snapshot.step_display}" with no valid '
                            f"user group selected. Skipping"
                        )
                else:
                    plan_line = (
                        f'escalation step "{escalation_policy_snapshot.step_display}" is slack specific. Skipping'
                    )
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
            else:
                users_to_notify = escalation_policy_snapshot.notify_to_users_queue

            for user_to_notify in users_to_notify:
                notification_plan_dict = self._get_notification_plan_for_user(
                    user_to_notify,
                    important=escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
                    for_slack=for_slack,
                    future_step=future_step,
                )
                for timedelta, notification_plan in notification_plan_dict.items():
                    escalation_plan_dict.setdefault(timedelta, []).extend(notification_plan)
        elif escalation_policy_snapshot.step in [
            EscalationPolicy.STEP_NOTIFY_SCHEDULE,
            EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
        ]:
            schedule = escalation_policy_snapshot.notify_schedule
            users_oncall = []
            if future_step:
                if schedule is not None:
                    step_datetime = timezone.now() + esc_timedelta
                    users_oncall = list_users_to_notify_from_ical(schedule, step_datetime)
                    important_text = ""
                    if escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT:
                        important_text = " (Important)"
                    plan_line = f"escalation step \"Notify on-call from Schedule '{schedule.name}'{important_text}\""
                    if users_oncall is None:
                        plan_line += ", but iCal import was failed. Skipping"
                    elif len(users_oncall) == 0:
                        plan_line += ", but there are no users to notify for this schedule slot. Skipping"
                else:
                    plan_line = (
                        f'escalation step "{escalation_policy_snapshot.step_display}", but schedule is '
                        f"unspecified. Skipping"
                    )
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
            else:
                users_oncall = escalation_policy_snapshot.notify_to_users_queue

            for user_to_notify in users_oncall:
                notification_plan_dict = self._get_notification_plan_for_user(
                    user_to_notify,
                    for_slack=for_slack,
                    important=escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
                    future_step=future_step,
                )
                # notification_plan_dict structure - {timedelta: [{"user_id": user.pk, "plan_lines": []}]
                for timedelta, notification_plan in notification_plan_dict.items():
                    escalation_plan_dict.setdefault(timedelta, []).extend(notification_plan)
        elif escalation_policy_snapshot.step == EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
            if future_step:
                custom_button = escalation_policy_snapshot.custom_button_trigger
                if custom_button is not None:
                    plan_line = f"trigger outgoing webhook `{custom_button.name}`"
                else:
                    plan_line = (
                        f'escalation step "{escalation_policy_snapshot.step_display}", '
                        f"but outgoing webhook is unspecified. Skipping"
                    )
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
        elif escalation_policy_snapshot.step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
            if future_step:
                if escalation_policy_snapshot.from_time is not None and escalation_policy_snapshot.to_time is not None:
                    plan_line = 'escalation step "Continue escalation if time"'
                else:
                    plan_line = 'escalation step "Continue escalation if time", but time is not configured. Skipping'
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
        elif escalation_policy_snapshot.step is None:
            if future_step:
                plan_line = "escalation step is unspecified. Skipping"
                plan = {"plan_lines": [plan_line]}
                escalation_plan_dict.setdefault(timedelta, []).append(plan)
        return escalation_plan_dict

    def _render_user_notification_line(self, user_to_notify, notification_policy, for_slack=False):
        """
        Renders user notification plan line
        :param user_to_notify:
        :param notification_policy:
        :param for_slack: (bool) add or not user slack id to user notification plan line
        :return: plan line
        """
        from apps.base.models import UserNotificationPolicy

        result = ""
        user_verbal = user_to_notify.get_username_with_slack_verbal() if for_slack else user_to_notify.username
        if notification_policy.step == UserNotificationPolicy.Step.NOTIFY:
            if notification_policy.notify_by == UserNotificationPolicy.NotificationChannel.SLACK:
                result += f"invite {user_verbal} in Slack"
            elif notification_policy.notify_by == UserNotificationPolicy.NotificationChannel.SMS:
                result += f"send sms to {user_verbal}"
            elif notification_policy.notify_by == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                result += f"call {user_verbal} by phone"
            elif notification_policy.notify_by == UserNotificationPolicy.NotificationChannel.TELEGRAM:
                result += f"send telegram message to {user_verbal}"
            else:
                try:
                    backend_id = UserNotificationPolicy.NotificationChannel(notification_policy.notify_by).name
                    backend = get_messaging_backend_from_id(backend_id)
                except ValueError:
                    pass
                else:
                    result += f"send {backend.label.lower() if backend else ''} message to {user_verbal}"
        if not result:
            result += f"inviting {user_verbal} but notification channel is unspecified"
        return result

    def _get_notification_plan_for_user(self, user_to_notify, future_step=False, important=False, for_slack=False):
        """
        Renders user notification plan
        :param user_to_notify:
        :param future_step:
        :param important:
        :param for_slack: (bool) add or not user slack id to user notification plan line
        :return: {timedelta: [{"user_id": user.pk, "plan_lines": [#rendered notification policy line, ]}, ...], ...}
        """
        from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

        timedelta = timezone.timedelta()
        is_the_first_notification_step = future_step  # escalation starts with this step or not

        # generate starter dict for notification plan
        plan_lines_dict = {
            "user_id": user_to_notify.pk,
            "plan_lines": [],
            "is_the_first_notification_step": is_the_first_notification_step,
        }
        notification_plan_dict = {timedelta: [plan_lines_dict]}

        last_user_log = None

        notification_policy_order = 0
        if not future_step:  # escalation step has been passed, so escalation for user has been already triggered.
            last_user_log = (
                user_to_notify.personal_log_records.filter(
                    alert_group=self.alert_group,
                    notification_policy__isnull=False,
                    type__in=[
                        UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
                        UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FINISHED,
                    ],
                )
                .order_by("created_at")
                .last()
            )

        if last_user_log and last_user_log.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED:
            if last_user_log.notification_policy is not None:
                notification_step = (
                    last_user_log.notification_step
                    if last_user_log.notification_step is not None
                    else last_user_log.notification_policy.step
                )
                # get order of the next notification step
                if notification_step == UserNotificationPolicy.Step.WAIT:
                    # do not exclude wait step, because we need it to count timedelta
                    notification_policy_order = last_user_log.notification_policy.order
                else:
                    # last passed step order + 1
                    notification_policy_order = last_user_log.notification_policy.order + 1

        notification_policies = UserNotificationPolicy.objects.filter(user=user_to_notify, important=important)

        for notification_policy in notification_policies:
            future_notification = notification_policy.order >= notification_policy_order
            if notification_policy.step == UserNotificationPolicy.Step.WAIT:
                wait_delay = notification_policy.wait_delay
                if wait_delay is not None:
                    timedelta += wait_delay  # increase timedelta for next steps
            elif future_notification:
                plan_line = self._render_user_notification_line(
                    user_to_notify, notification_policy, for_slack=for_slack
                )
                # add plan_line to user plan_lines list
                if not notification_plan_dict.get(timedelta):
                    plan = {"user_id": user_to_notify.pk, "plan_lines": [plan_line]}
                    notification_plan_dict.setdefault(timedelta, []).append(plan)
                else:
                    notification_plan_dict[timedelta][0]["plan_lines"].append(plan_line)
        return notification_plan_dict
