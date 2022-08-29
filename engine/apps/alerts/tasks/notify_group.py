from django.apps import apps
from django.conf import settings

from apps.slack.scenarios import scenario_step
from apps.slack.tasks import check_slack_message_exists_before_post_message_to_thread
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .notify_user import notify_user_task
from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_group_task(alert_group_pk, escalation_policy_snapshot_order=None):
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
    UserNotificationPolicy = apps.get_model("base", "UserNotificationPolicy")
    EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    EscalationDeliveryStep = scenario_step.ScenarioStep.get_step("escalation_delivery", "EscalationDeliveryStep")

    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    organization = alert_group.channel.organization
    slack_team_identity = organization.slack_team_identity
    if not slack_team_identity:
        task_logger.info(
            f"Failed to notify user group for alert_group {alert_group_pk} because slack team identity doesn't exist"
        )
        return
    step = EscalationDeliveryStep(slack_team_identity, organization)

    escalation_snapshot = alert_group.escalation_snapshot
    escalation_policy_snapshot = escalation_snapshot.escalation_policies_snapshots[escalation_policy_snapshot_order]
    escalation_policy_pk = escalation_policy_snapshot.id
    escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()
    escalation_policy_step = escalation_policy_snapshot.step
    usergroup = escalation_policy_snapshot.notify_to_group

    usergroup_users = usergroup.get_users_from_members_for_organization(organization)

    if len(usergroup_users) == 0:
        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
            alert_group=alert_group,
            escalation_policy=escalation_policy,
            escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_USER_GROUP_IS_EMPTY,
            escalation_policy_step=escalation_policy_step,
        )
        log_record.save()
    else:
        if escalation_snapshot is not None:
            escalation_policy_snapshot.notify_to_users_queue = usergroup_users
            escalation_snapshot.save_to_alert_group()

        usergroup_notification_plan = ""
        for user in usergroup_users:
            if not user.is_notification_allowed:
                continue

            notification_policies = UserNotificationPolicy.objects.filter(
                user=user,
                important=escalation_policy_step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
            )
            usergroup_notification_plan += "\n_{} (".format(
                step.get_user_notification_message_for_thread_for_usergroup(user, notification_policies.first())
            )
            notification_channels = []
            if notification_policies.filter(step=UserNotificationPolicy.Step.NOTIFY).count() == 0:
                usergroup_notification_plan += "Empty notifications"
            for notification_policy in notification_policies:
                if notification_policy.step == UserNotificationPolicy.Step.NOTIFY:
                    notification_channels.append(
                        UserNotificationPolicy.NotificationChannel(notification_policy.notify_by).label
                    )
            usergroup_notification_plan += "→".join(notification_channels) + ")_"
            reason = f"Membership in <!subteam^{usergroup.slack_id}> User Group"

            notify_user_task.apply_async(
                args=(
                    user.pk,
                    alert_group.pk,
                ),
                kwargs={
                    "reason": reason,
                    "prevent_posting_to_thread": True,
                    "important": escalation_policy_step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
                },
            )
            AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
                author=user,
                alert_group=alert_group,
                reason=reason,
                escalation_policy=escalation_policy,
                escalation_policy_step=escalation_policy_step,
            ).save()
        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
            alert_group=alert_group,
            escalation_policy=escalation_policy,
            escalation_policy_step=escalation_policy_step,
            step_specific_info={"usergroup_handle": usergroup.handle},
        )
        log_record.save()
        if not alert_group.skip_escalation_in_slack and alert_group.notify_in_slack_enabled:
            text = f"Inviting @{usergroup.handle} User Group: {usergroup_notification_plan}"
            step_specific_info = {"usergroup_handle": usergroup.handle}
            # Start task that checks if slack message exists every 10 seconds for 24 hours and publish message
            # to thread if it does.
            check_slack_message_exists_before_post_message_to_thread.apply_async(
                args=(alert_group_pk, text),
                kwargs={
                    "escalation_policy_pk": escalation_policy_pk,
                    "escalation_policy_step": escalation_policy_step,
                    "step_specific_info": step_specific_info,
                },
                countdown=5,
            )
    task_logger.debug(
        f"Finish notify_group_task for alert_group {alert_group_pk}, log record {log_record.pk}",
    )
