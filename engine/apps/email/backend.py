import typing

from apps.base.messaging import BaseMessagingBackend
from apps.email.tasks import notify_user_async

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.base.models import UserNotificationPolicy
    from apps.user_management.models import User


class EmailBackend(BaseMessagingBackend):
    backend_id = "EMAIL"
    label = "Email"
    short_label = "Email"
    available_for_use = True

    templater = "apps.email.alert_rendering.AlertEmailTemplater"
    template_fields = ("title", "message")

    def serialize_user(self, user: "User"):
        return {"email": user.email}

    def notify_user(
        self, user: "User", alert_group: "AlertGroup", notification_policy: typing.Optional["UserNotificationPolicy"]
    ):
        """
        NOTE: `notification_policy` may be None if the user has no notification policies defined, as
        email is the default backend used
        """
        notify_user_async.delay(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk if notification_policy else None,
        )
