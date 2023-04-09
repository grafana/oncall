from django.db import models


class OnCallPhoneCall(models.Model):

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey(
        "alerts.Alert", on_delete=models.SET_NULL, null=True, default=None
    )  # deprecareed
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)

    grafana_cloud_notification = models.BooleanField(default=False)  # rename
