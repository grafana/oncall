import datetime
import logging

from django.db import models, transaction

from apps.alerts import tasks

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Invitation(models.Model):
    """
    It's an invitation of a user to join working on Alert Group
    """

    ATTEMPTS_LIMIT = 10

    time_deltas_by_attempts = [
        datetime.timedelta(minutes=6),
        datetime.timedelta(minutes=16),
        datetime.timedelta(minutes=31),
        datetime.timedelta(hours=1, minutes=1),
        datetime.timedelta(hours=3, minutes=1),
    ]

    author = models.ForeignKey(
        "user_management.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="author_of_invitations",
    )

    invitee = models.ForeignKey(
        "user_management.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="invitee_in_invitations",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.CASCADE, related_name="invitations")
    attempt = models.IntegerField(default=0)

    @property
    def attempts_left(self):
        return Invitation.ATTEMPTS_LIMIT - self.attempt

    @staticmethod
    def get_delay_by_attempt(attempt):
        countdown = Invitation.time_deltas_by_attempts[-1]
        if attempt < len(Invitation.time_deltas_by_attempts):
            countdown = Invitation.time_deltas_by_attempts[attempt]
        return countdown

    @staticmethod
    def invite_user(invitee_user, alert_group, user):
        from apps.alerts.models import AlertGroupLogRecord

        # RFCT - why atomic? without select for update?
        with transaction.atomic():
            try:
                invitation = Invitation.objects.get(
                    invitee=invitee_user,
                    alert_group=alert_group,
                    is_active=True,
                )
                invitation.is_active = False
                invitation.save(update_fields=["is_active"])
                log_record = AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_RE_INVITE, author=user, alert_group=alert_group
                )
            except Invitation.DoesNotExist:
                log_record = AlertGroupLogRecord(
                    type=AlertGroupLogRecord.TYPE_INVITE,
                    author=user,
                    alert_group=alert_group,
                )
            invitation = Invitation(
                invitee=invitee_user,
                alert_group=alert_group,
                is_active=True,
                author=user,
            )
            invitation.save()

        log_record.invitation = invitation
        log_record.save()
        logger.debug(
            f"call send_alert_group_signal for alert_group {alert_group.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}'"
        )

        tasks.send_alert_group_signal.apply_async((log_record.pk,))
        tasks.invite_user_to_join_incident.apply_async((invitation.pk,))

    @staticmethod
    def stop_invitation(invitation_pk, user):
        from apps.alerts.models import AlertGroupLogRecord

        with transaction.atomic():
            try:
                invitation = Invitation.objects.filter(pk=invitation_pk).select_for_update()[0]
            except IndexError:
                return f"stop_invitation: Invitation with pk {invitation_pk} doesn't exist"
            invitation.is_active = False
            invitation.save(update_fields=["is_active"])

            log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_STOP_INVITATION,
                author=user,
                alert_group=invitation.alert_group,
                invitation=invitation,
            )

        log_record.save()
        logger.debug(
            f"call send_alert_group_signal for alert_group {invitation.alert_group.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}'"
        )
        tasks.send_alert_group_signal.apply_async((log_record.pk,))
