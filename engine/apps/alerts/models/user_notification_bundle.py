import datetime

from django.db import models
from django.utils import timezone

from apps.alerts.constants import BUNDLED_NOTIFICATION_DELAY_SECONDS
from apps.base.models import UserNotificationPolicy


class UserNotificationBundle(models.Model):
    NOTIFICATION_CHANNELS_TO_BUNDLE = [
        UserNotificationPolicy.NotificationChannel.SMS,
    ]

    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name="notification_bundles")
    important = models.BooleanField()
    notification_channel = models.PositiveSmallIntegerField(default=0)
    last_notified = models.DateTimeField(default=None, null=True)
    notification_task_id = models.CharField(max_length=100, null=True, default=None)
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
        """
        `eta` shows eta of scheduled send_bundled_notification task and should never be less than the current time
        (with a 1 minute buffer provided).
        `eta` is None means that there is no scheduled task.
        """
        if not self.eta or self.eta + timezone.timedelta(minutes=1) >= timezone.now():
            return True
        return False

    def get_notification_eta(self) -> datetime.datetime:
        last_notified = self.last_notified if self.last_notified else timezone.now()
        return last_notified + timezone.timedelta(seconds=BUNDLED_NOTIFICATION_DELAY_SECONDS)

    def append_notification(self, alert_group, notification_policy):
        self.notifications.create(alert_group=alert_group, notification_policy=notification_policy)


class BundledNotification(models.Model):
    alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.CASCADE)
    notification_policy = models.ForeignKey("base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True)
    notification_bundle = models.ForeignKey(
        UserNotificationBundle, on_delete=models.CASCADE, related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    bundle_uuid = models.CharField(max_length=100, null=True, default=None, db_index=True)
