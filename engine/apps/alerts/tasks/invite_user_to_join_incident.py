import humanize
from django.conf import settings
from django.db import transaction
from django.db.models import F

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .notify_user import notify_user_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def invite_user_to_join_incident(invitation_pk):
    from apps.alerts.models import AlertGroupLogRecord, Invitation

    with transaction.atomic():
        try:
            invitation = Invitation.objects.filter(pk=invitation_pk).select_for_update()[0]
        except IndexError:
            return f"invite_user_to_join_incident: Invitation with pk {invitation_pk} doesn't exist"

        if not invitation.is_active:
            return None
        if invitation.attempts_left <= 0 or invitation.alert_group.resolved:
            invitation.is_active = False
            invitation.save(update_fields=["is_active"])
            return None

        delay = Invitation.get_delay_by_attempt(invitation.attempt)

        user_verbal = invitation.author.get_username_with_slack_verbal(mention=True)
        reason = "Invitation activated by {}. Will try again in {} (attempt {}/{})".format(
            user_verbal,
            humanize.naturaldelta(delay),
            invitation.attempt + 1,
            Invitation.ATTEMPTS_LIMIT,
        )

        notify_task = notify_user_task.signature(
            (
                invitation.invitee.pk,
                invitation.alert_group.pk,
            ),
            {
                "reason": reason,
                "notify_even_acknowledged": True,
                "notify_anyway": True,
                "important": True,
            },
            immutable=True,
        )

        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_INVITATION_TRIGGERED,
            author=None,
            alert_group=invitation.alert_group,
            invitation=invitation,
        )
        log_record.save()

        invitation_task = invite_user_to_join_incident.signature(
            (invitation.pk,), countdown=delay.total_seconds(), immutable=True
        )
        notify_task.apply_async()
        invitation_task.apply_async()

        invitation.attempt = F("attempt") + 1
        invitation.save()
