import asyncio

from typing import Optional

from celery.utils.log import get_task_logger
from django.conf import settings


from apps.matrix.client import MatrixClient
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


logger = get_task_logger(__name__)

_client: Optional[MatrixClient] = None
client_lock = asyncio.Lock()


async def get_client():
    global _client
    async with client_lock:
        if _client is None:
            _client = await MatrixClient.login_with_username_and_password(
                settings.MATRIX_USER_ID,
                settings.MATRIX_PASSWORD,
                "grafana-matrix-integration",
                settings.MATRIX_HOMESERVER
            )
        return _client


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1)
async def notify_user_via_matrix(user, alert_group, notification_policy, paging_room_id, message):
    # imported here to avoid circular import error
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    client = await get_client()

    if not await client.is_in_room(paging_room_id):
        # TODO - error checking is particularly important here - you can visually check that your user_id
        # exists and is correct, but you can't check that the bot's able to join a room without actually having it
        # try to do so.
        # (To be clear - what is currently here is _probably_ insufficient, but I'm reliant on the Oncall team
        # to tell me how to raise an "out-of-band" error)
        try:
            await client.join_room(paging_room_id)
        except Exception as e:
            UserNotificationPolicyLogRecord.objects.create(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="error while sending Matrix message",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by
            )
            logger.error(f"Unable to join paging_room {paging_room_id} to notify user {user.pk}:")
            logger.exception(e)
            return

    await client.send_message_to_room(
        paging_room_id,
        message['raw'],
        message['formatted'])
