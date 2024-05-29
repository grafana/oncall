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
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord, EscalationPolicy
    from apps.base.models import UserNotificationPolicy

    EscalationDeliveryStep = scenario_step.ScenarioStep.get_step("escalation_delivery", "EscalationDeliveryStep")

    alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    # check alert group state before notifying all users in the group
    if alert_group.resolved or alert_group.acknowledged or alert_group.silenced:
        task_logger.info(f"alert_group {alert_group.pk} was resolved, acked or silenced. No need to notify group")
        return

    organization = alert_group.channel.organization
    slack_team_identity = organization.slack_team_identity
    if not slack_team_identity:
        task_logger.info(
            f"Failed to notify user group for alert_group {alert_group_pk} because slack team identity doesn't exist"
        )
        return
    step = EscalationDeliveryStep(slack_team_identity, organization)

    escalation_snapshot = alert_group.escalation_snapshot
    try:
        # escalation_policy_snapshot_order refers to order as defined in the policy,
        # which is unique but not necessarily sequential and may not start from zero
        escalation_policy_snapshot = [
            policy
            for policy in escalation_snapshot.escalation_policies_snapshots
            if policy.order == escalation_policy_snapshot_order
        ][0]
    except IndexError:
        escalation_policy_snapshot = None

    if not escalation_policy_snapshot:
        # The step has an incorrect order. Probably the order was changed manually with terraform.
        # It is a quick fix, tasks notify_all_task and notify_group_task should be refactored to avoid getting snapshot
        # by order
        task_logger.warning(
            f"escalation_policy_snapshot for alert_group {alert_group.pk} with order "
            f"{escalation_policy_snapshot_order} is not found. Skip step"
        )
        return

    escalation_policy_pk = escalation_policy_snapshot.id
    escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()
    escalation_policy_step = escalation_policy_snapshot.step
    usergroup = escalation_policy_snapshot.notify_to_group

    usergroup_users = []
    if usergroup is not None:
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

            important = escalation_policy_step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT
            notification_policies = user.get_or_create_notification_policies(important=important)

            if notification_policies:
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
