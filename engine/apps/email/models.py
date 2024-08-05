import uuid

from django.db import models


class EmailMessageQuerySet(models.QuerySet):
    def create(self, **kwargs):
        from apps.base.models.user_notification_policy_log_record import (
            _check_if_notification_policy_is_transient_fallback,
        )

        _check_if_notification_policy_is_transient_fallback(kwargs)
        return super().create(**kwargs)


class EmailMessage(models.Model):
    objects = EmailMessageQuerySet.as_manager()

    message_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey("alerts.Alert", on_delete=models.SET_NULL, null=True, default=None)
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
