from django.db import models


# Duplicate to avoid circular import to provide values for status field
class TwilioCallStatuses:
    QUEUED = 10
    RINGING = 20
    IN_PROGRESS = 30
    COMPLETED = 40
    BUSY = 50
    FAILED = 60
    NO_ANSWER = 70
    CANCELED = 80

    CHOICES = (
        (QUEUED, "queued"),
        (RINGING, "ringing"),
        (IN_PROGRESS, "in-progress"),
        (COMPLETED, "completed"),
        (BUSY, "busy"),
        (FAILED, "failed"),
        (NO_ANSWER, "no-answer"),
        (CANCELED, "canceled"),
    )


class PhoneCallRecord(models.Model):

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey(
        "alerts.Alert", on_delete=models.SET_NULL, null=True, default=None
    )  # deprecateed
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)

    grafana_cloud_notification = models.BooleanField(default=False)  # rename

    # deprecated. It's here for backward compatibility for calls made during or shortly before migration.
    # Should be removed soon after migration
    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=TwilioCallStatuses.CHOICES,
    )

    sid = models.CharField(
        blank=True,
        max_length=50,
    )
