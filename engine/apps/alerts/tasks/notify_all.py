from django.apps import apps
from django.conf import settings

from apps.slack.tasks import check_slack_message_exists_before_post_message_to_thread
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .notify_user import notify_user_task
from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_all_task(alert_group_pk, escalation_policy_snapshot_order=None):
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
    EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")
    AlertGroup = apps.get_model("alerts", "AlertGroup")

    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    escalation_snapshot = alert_group.escalation_snapshot
    escalation_policy_snapshot = escalation_snapshot.escalation_policies_snapshots[escalation_policy_snapshot_order]
    escalation_policy_pk = escalation_policy_snapshot.id
    escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()
    escalation_policy_step = escalation_policy_snapshot.step
    slack_channel_id = escalation_snapshot.slack_channel_id

    countdown = 0
    slack_team_identity = alert_group.channel.organization.slack_team_identity

    AlertGroupLogRecord(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        author=None,
        alert_group=alert_group,
        escalation_policy=escalation_policy,
        escalation_policy_step=escalation_policy_step,
    ).save()

    # we cannot notify a slack channel if team does not have slack team identity,
    # because we make a request to slack to get channel members
    if slack_team_identity is None or slack_channel_id is None:
        AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
            alert_group=alert_group,
            escalation_policy=escalation_policy,
            escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IN_SLACK,
            escalation_policy_step=escalation_policy_step,
        ).save()
        task_logger.debug(
            f"Failed to notify slack channel for alert_group {alert_group_pk} because slack team identity doesn't exist"
        )
        return

    # get users to notify
    users = slack_team_identity.get_users_from_slack_conversation_for_organization(
        channel_id=slack_channel_id,
        organization=alert_group.channel.organization,
    )

    if escalation_snapshot is not None:
        escalation_policy_snapshot.notify_to_users_queue = users
        escalation_snapshot.save_to_alert_group()

    for user in users:
        reason = "notifying everyone in the channel"

        notify_user_task.apply_async(
            args=(
                user.pk,
                alert_group.pk,
            ),
            kwargs={"reason": reason, "prevent_posting_to_thread": True},
            countdown=countdown,
        )
        countdown += 1
        AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
            author=user,
            alert_group=alert_group,
            reason=reason.title(),
            escalation_policy=escalation_policy,
            escalation_policy_step=escalation_policy_step,
        ).save()

    if not alert_group.skip_escalation_in_slack and alert_group.notify_in_slack_enabled:
        text = "Inviting <!channel>. Reason: *Notify All* Step"
        # Start task that checks if slack message exists every 10 seconds for 24 hours and publish message
        # to thread if it does.
        check_slack_message_exists_before_post_message_to_thread.apply_async(
            args=(alert_group_pk, text),
            kwargs={
                "escalation_policy_pk": escalation_policy_pk,
                "escalation_policy_step": escalation_policy_step,
            },
            countdown=5,
        )
