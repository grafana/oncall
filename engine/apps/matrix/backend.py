from apps.base.messaging import BaseMessagingBackend
from apps.matrix.alert_rendering import build_raw_and_formatted_message

import asyncio

from apps.matrix.tasks import notify_user_via_matrix

import logging
logger = logging.getLogger(__name__)


class MatrixBackend(BaseMessagingBackend):
    backend_id = "MATRIX"
    label = "Matrix"  # TODO - it'd be cool to add an icon of the Matrix logo here!
    short_label = "Matrix"
    available_for_use = True

    templater = "apps.matrix.alert_rendering.AlertMatrixTemplater"
    template_fields = ("title", "message")

    def serialize_user(self, user):
        return {key: repr(getattr(user, key)) for key in ['user_id', 'name', 'matrix_user_identity']}

    def notify_user(self, user, alert_group, notification_policy):
        from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

        if not user.matrix_user_identity:
            UserNotificationPolicyLogRecord.objects.create(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="Error while sending Matrix message",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by
            )
            logger.error(f"Error while sending Matrix message - no matrix_user_identity for user {user.pk}")
            return

        paging_room_id = user.matrix_user_identity.paging_room_id
        message = build_raw_and_formatted_message(alert_group, user.matrix_user_identity)
        # The reason for the split in logic between everything above and below this line:
        # * interactions with Django model object properties (e.g. `user.matrix_user_identity`) cannot
        #     be carried out in an async context.
        # * calls to Matrix via matrix-nio are heavily encouraged to be made asynchronously rather
        #     than synchronously.
        asyncio.run(notify_user_via_matrix(
            user, alert_group, notification_policy, paging_room_id, message))

