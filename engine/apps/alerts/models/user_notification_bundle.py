import datetime
import typing

from django.db import models
from django.utils import timezone

from apps.alerts.constants import BUNDLED_NOTIFICATION_DELAY_SECONDS
from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import validate_channel_choice

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, AlertReceiveChannel
    from apps.user_management.models import User


class UserNotificationBundle(models.Model):
    user: "User"
    notifications: "RelatedManager['BundledNotification']"

    NOTIFICATION_CHANNELS_TO_BUNDLE = [
        UserNotificationPolicy.NotificationChannel.SMS,
    ]

    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name="notification_bundles")
    important = models.BooleanField()
    notification_channel = models.PositiveSmallIntegerField(
        validators=[validate_channel_choice], null=True, default=None
    )
    last_notified_at = models.DateTimeField(default=None, null=True)
    notification_task_id = models.CharField(max_length=100, null=True, default=None)
    # estimated time of arrival for scheduled send_bundled_notification task
    eta = models.DateTimeField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "important", "notification_channel"], name="unique_user_notification_bundle"
            )
        ]

    def notified_recently(self) -> bool:
        return (
            timezone.now() - self.last_notified_at < timezone.timedelta(seconds=BUNDLED_NOTIFICATION_DELAY_SECONDS)
            if self.last_notified_at
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
        last_notified = self.last_notified_at if self.last_notified_at else timezone.now()
        return last_notified + timezone.timedelta(seconds=BUNDLED_NOTIFICATION_DELAY_SECONDS)

    def append_notification(self, alert_group: "AlertGroup", notification_policy: "UserNotificationPolicy"):
        self.notifications.create(
            alert_group=alert_group, notification_policy=notification_policy, alert_receive_channel=alert_group.channel
        )

    @classmethod
    def notification_is_bundleable(cls, notification_channel):
        return notification_channel in cls.NOTIFICATION_CHANNELS_TO_BUNDLE


class BundledNotification(models.Model):
    alert_group: "AlertGroup"
    alert_receive_channel: "AlertReceiveChannel"
    notification_policy: typing.Optional["UserNotificationPolicy"]
    notification_bundle: "UserNotificationBundle"

    alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.CASCADE, related_name="bundled_notifications")
    alert_receive_channel = models.ForeignKey("alerts.AlertReceiveChannel", on_delete=models.CASCADE)
    notification_policy = models.ForeignKey("base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True)
    notification_bundle = models.ForeignKey(
        UserNotificationBundle, on_delete=models.CASCADE, related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    bundle_uuid = models.CharField(max_length=100, null=True, default=None, db_index=True)
