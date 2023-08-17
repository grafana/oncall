import logging

from celery import uuid as celery_uuid
from celery.utils.log import get_task_logger
from django.conf import settings
from telegram import error

from apps.alerts.models import Alert, AlertGroup
from apps.base.models import UserNotificationPolicy
from apps.telegram.client import TelegramClient
from apps.telegram.decorators import (
    handle_missing_token,
    ignore_bot_deleted,
    ignore_message_to_edit_deleted,
    ignore_message_unchanged,
    ignore_reply_to_message_deleted,
)
from apps.telegram.models import TelegramMessage, TelegramToOrganizationConnector
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import OkToRetry

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
@handle_missing_token
def register_telegram_webhook(token=None):
    if settings.FEATURE_TELEGRAM_LONG_POLLING_ENABLED:
        return

    telegram_client = TelegramClient(token=token)

    try:
        telegram_client.register_webhook()
    except (error.InvalidToken, error.Unauthorized, error.BadRequest) as e:
        logger.warning(f"Tried to register Telegram webhook using token: {telegram_client.token}, got error: {e}")


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
@ignore_message_unchanged
@ignore_message_to_edit_deleted
@ignore_bot_deleted
def edit_message(self, message_pk):
    message = TelegramMessage.objects.get(pk=message_pk)
    telegram_client = TelegramClient()

    # if edit_task_id was not set at the time task was invoked, assign it and rerun the task
    if message.edit_task_id is None:
        task_id = celery_uuid()
        message.edit_task_id = task_id
        message.save(update_fields=["edit_task_id"])

        edit_message.apply_async((message_pk,), task_id=task_id)
        return

    if message.edit_task_id != edit_message.request.id:
        logger.debug("Dropping the task since another task was scheduled already.")
        return

    try:
        telegram_client.edit_message(message=message)
    except error.BadRequest as e:
        if "Message is not modified" in e.message:
            pass
    except (error.RetryAfter, error.TimedOut) as e:
        countdown = getattr(e, "retry_after", 3)

        task_id = celery_uuid()
        message.edit_task_id = task_id
        message.save(update_fields=["edit_task_id"])

        edit_message.apply_async((message_pk,), countdown=countdown, task_id=task_id)
        return

    message.edit_task_id = None
    message.save(update_fields=["edit_task_id"])


@shared_dedicated_queue_retry_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=None)
def send_link_to_channel_message_or_fallback_to_full_alert_group(
    self, alert_group_pk, notification_policy_pk, user_connector_pk
):
    from apps.telegram.models import TelegramToUserConnector

    try:
        user_connector = TelegramToUserConnector.objects.get(pk=user_connector_pk)
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)

        # probably telegram message just didn't appear in Telegram channel yet
        if self.request.retries <= 10:
            user_connector.send_link_to_channel_message(
                alert_group=alert_group, notification_policy=notification_policy
            )
        else:
            # seems like the message won't appear in Telegram channel, so send the full alert group to user
            user_connector.send_full_alert_group(alert_group=alert_group, notification_policy=notification_policy)
    except TelegramToUserConnector.DoesNotExist:
        # Handle cases when user deleted the bot while escalation is active
        logger.warning(
            f"TelegramToUserConnector {user_connector_pk} not found. "
            f"Most probably it was deleted while escalation was in progress."
            f"alert_group {alert_group_pk}"
        )
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(
            f"UserNotificationPolicy {notification_policy_pk} does not exist for alert group {alert_group_pk}"
        )


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
@handle_missing_token
@ignore_reply_to_message_deleted
@ignore_bot_deleted
def send_log_and_actions_message(self, channel_chat_id, group_chat_id, channel_message_id, reply_to_message_id):
    with OkToRetry(task=self, exc=TelegramMessage.DoesNotExist, num_retries=5):
        try:
            channel_message = TelegramMessage.objects.get(chat_id=channel_chat_id, message_id=channel_message_id)
        except TelegramMessage.DoesNotExist:
            if self.request.retries <= 5:
                raise
            else:
                logger.warning(
                    f"Could not send log and actions message, telegram message does not exist "
                    f" chat_id={channel_chat_id} message_id={channel_message_id}"
                )
                return

        if channel_message.discussion_group_message_id is None:
            channel_message.discussion_group_message_id = reply_to_message_id
            channel_message.save(update_fields=["discussion_group_message_id"])

        alert_group = channel_message.alert_group

        log_message_sent = alert_group.telegram_messages.filter(message_type=TelegramMessage.LOG_MESSAGE).exists()
        actions_message_sent = alert_group.telegram_messages.filter(
            message_type=TelegramMessage.ACTIONS_MESSAGE
        ).exists()

        telegram_client = TelegramClient()
        with OkToRetry(
            task=self, exc=(error.RetryAfter, error.TimedOut), compute_countdown=lambda e: getattr(e, "retry_after", 3)
        ):
            try:
                if not log_message_sent:
                    telegram_client.send_message(
                        chat_id=group_chat_id,
                        message_type=TelegramMessage.LOG_MESSAGE,
                        alert_group=alert_group,
                        reply_to_message_id=reply_to_message_id,
                    )
                if not actions_message_sent:
                    telegram_client.send_message(
                        chat_id=group_chat_id,
                        message_type=TelegramMessage.ACTIONS_MESSAGE,
                        alert_group=alert_group,
                        reply_to_message_id=reply_to_message_id,
                    )
            except error.BadRequest as e:
                if e.message == "Chat not found":
                    logger.warning(
                        f"Could not send log and actions messages to Telegram group with id {group_chat_id} "
                        f"due to 'Chat not found'. alert_group {alert_group.pk}"
                    )
                    return
                else:
                    raise


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
@handle_missing_token
@ignore_bot_deleted
@ignore_reply_to_message_deleted
def on_create_alert_telegram_representative_async(self, alert_pk):
    """
    It's async in order to prevent Telegram downtime or formatting issues causing delay with SMS and other destinations.
    """

    alert = Alert.objects.get(pk=alert_pk)
    alert_group = alert.group

    alert_group_messages = alert_group.telegram_messages.filter(
        message_type__in=[
            TelegramMessage.ALERT_GROUP_MESSAGE,
            TelegramMessage.PERSONAL_MESSAGE,
            TelegramMessage.FORMATTING_ERROR,
        ]
    )
    # TODO: discuss moving this logic into .send_alert_group_message

    telegram_channel = TelegramToOrganizationConnector.get_channel_for_alert_group(alert_group)

    if telegram_channel is not None and not alert_group_messages.exists():
        with OkToRetry(
            task=self,
            exc=(error.RetryAfter, error.TimedOut),
            compute_countdown=lambda e: getattr(e, "retry_after", 3),
        ):
            telegram_channel.send_alert_group_message(alert_group)

    messages_to_edit = alert_group_messages.filter(
        message_type__in=(
            TelegramMessage.ALERT_GROUP_MESSAGE,
            TelegramMessage.PERSONAL_MESSAGE,
        )
    )
    for message in messages_to_edit:
        edit_message.delay(message_pk=message.pk)
