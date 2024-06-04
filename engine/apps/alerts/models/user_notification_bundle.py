import datetime

from django.db import models
from django.utils import timezone

from apps.alerts.constants import BUNDLED_NOTIFICATION_DELAY_SECONDS
from apps.base.models import UserNotificationPolicy


class UserNotificationBundle(models.Model):
    NOTIFICATION_CHANNELS_TO_BUNDLE = [
        UserNotificationPolicy.NotificationChannel.SMS,
    ]

    user = models.ForeignKey(
        "user_management.User",
        on_delete=models.CASCADE,
    )
    important = models.BooleanField()
    notification_channel = models.PositiveSmallIntegerField(default=0)
    last_notified = models.DateTimeField(default=None, null=True)
    notification_task_id = models.CharField(max_length=100, null=True, default=None)
    # list with alert groups info to build notification message:
    # [{"alert_group_id": 1, "integration_name": "Test", "notification_policy_id": 1}]
    notification_data = models.JSONField(default=list)
    # estimated time of arrival for notification bundle
    eta = models.DateTimeField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "important", "notification_channel"], name="unique_user_notification_bundle"
            )
        ]

    def notified_recently(self) -> bool:
        return (
            timezone.now() - self.last_notified < timezone.timedelta(seconds=BUNDLED_NOTIFICATION_DELAY_SECONDS)
            if self.last_notified
            else False
        )

    def eta_is_valid(self) -> bool:
        if not self.eta or self.eta + timezone.timedelta(minutes=1) >= timezone.now():
            return True
        return False

    def get_notification_eta(self) -> datetime.datetime:
        last_notified = self.last_notified if self.last_notified else timezone.now()
        return last_notified + timezone.timedelta(seconds=BUNDLED_NOTIFICATION_DELAY_SECONDS)
