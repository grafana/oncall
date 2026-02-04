import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status

from apps.alerts.models import Alert, AlertGroup
from apps.zoom.alert_rendering import AlertGroupZoomRenderer, ZoomMessageRenderer
from apps.zoom.client import ZoomClient
from apps.zoom.exceptions import ZoomAPIException, ZoomAPITokenInvalid
from apps.zoom.models import ZoomChannel, ZoomMessage
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import OkToRetry

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_create_alert_async(self, alert_pk):
    """
    Send alert notification to Zoom Team Chat channel.
    
    This is async to prevent Zoom downtime or formatting issues from causing delays
    with SMS and other notification destinations.
    """
    try:
        alert = Alert.objects.get(pk=alert_pk)
    except Alert.DoesNotExist as e:
        if on_create_alert_async.request.retries >= 10:
            logger.error(f"Alert {alert_pk} was not found. Probably it was deleted. Stop retrying")
            return
        else:
            raise e

    alert_group = alert.group
    zoom_channel = ZoomChannel.get_channel_for_alert_group(alert_group=alert_group)
    
    if not zoom_channel:
        logger.info(f"No Zoom channel found for alert {alert_pk}. Skipping Zoom notification.")
        return

    # Check if a message already exists for this alert group
    message = alert_group.zoom_messages.filter(message_type=ZoomMessage.ALERT_GROUP_MESSAGE).first()
    if message:
        logger.info(f"Zoom message already exists with message_id {message.message_id}. Skipping creation.")
        return

    # Render the message
    renderer = ZoomMessageRenderer(alert_group)
    message_content = renderer.render_alert_group_message()

    with OkToRetry(task=self, exc=(ZoomAPIException,), num_retries=3):
        try:
            client = ZoomClient()
            # Use send_channel_message_with_body for full control
            zoom_message = client.send_channel_message_with_body(
                channel_id=zoom_channel.channel_id,
                header_text=message_content.get("header", "OnCall Alert"),
                sub_header_text=message_content.get("sub_header"),
                body=message_content.get("body", []),
            )
        except ZoomAPITokenInvalid:
            logger.error(f"Zoom API token is invalid. Could not create message for alert {alert_pk}")
            return
        except ZoomAPIException as ex:
            logger.error(f"Zoom API error: {ex}")
            if ex.status not in [status.HTTP_401_UNAUTHORIZED]:
                raise ex
            return
        else:
            ZoomMessage.create_message(
                alert_group=alert_group,
                message_id=zoom_message.message_id,
                channel_id=zoom_channel.channel_id,
                message_type=ZoomMessage.ALERT_GROUP_MESSAGE,
            )
            logger.info(f"Created Zoom message {zoom_message.message_id} for alert group {alert_group.pk}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_alert_group_action_triggered_async(log_record_id):
    """
    Update Zoom message when an alert group action is triggered.
    """
    from apps.alerts.models import AlertGroupLogRecord
    from apps.zoom.alert_group_representative import AlertGroupZoomRepresentative

    try:
        log_record = AlertGroupLogRecord.objects.get(pk=log_record_id)
    except AlertGroupLogRecord.DoesNotExist as e:
        logger.warning(f"Zoom representative: log record {log_record_id} never created or has been deleted")
        raise e

    alert_group_id = log_record.alert_group_id

    # Check if there's a Zoom message for this alert group
    try:
        log_record.alert_group.zoom_messages.get(message_type=ZoomMessage.ALERT_GROUP_MESSAGE)
    except ZoomMessage.DoesNotExist as e:
        if on_alert_group_action_triggered_async.request.retries >= 10:
            logger.error(f"Zoom message not created for alert group {alert_group_id}. Stop retrying")
            return
        else:
            raise e

    logger.info(
        f"Start Zoom on_alert_group_action_triggered for alert_group {alert_group_id}, log record {log_record_id}"
    )
    
    representative = AlertGroupZoomRepresentative(log_record)
    if representative.is_applicable():
        handler = representative.get_handler()
        handler(log_record.alert_group)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_user_about_alert_async(user_pk, alert_group_pk, notification_policy_pk):
    """
    Send a personal notification to a user via Zoom Team Chat.
    """
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    def _create_error_log_record(notification_error_code=None):
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error during Zoom notification",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
            notification_error_code=notification_error_code,
        )

    try:
        user = User.objects.get(pk=user_pk)
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
        zoom_message = alert_group.zoom_messages.get(message_type=ZoomMessage.ALERT_GROUP_MESSAGE)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} is not found")
        return
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} is not found")
        return
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"UserNotificationPolicy {notification_policy_pk} is not found")
        return
    except ZoomMessage.DoesNotExist as e:
        if notify_user_about_alert_async.request.retries >= 10:
            logger.error(
                f"Alert group Zoom message is not created for {alert_group_pk}. "
                "Stopped retrying for user notification"
            )
            _create_error_log_record(
                UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_ZOOM_ALERT_GROUP_MESSAGE_NOT_FOUND
            )
            return
        else:
            raise e

    zoom_channel = ZoomChannel.get_channel_for_alert_group(alert_group=alert_group)
    if not zoom_channel:
        logger.error(f"Zoom channel not found for user notification {user_pk}")
        return

    templated_alert = AlertGroupZoomRenderer(alert_group).alert_renderer.templated_alert

    # Build the notification message
    # Use try/except to handle RelatedObjectDoesNotExist for OneToOneField
    try:
        zoom_user_identity = user.zoom_user_identity
        # Use Zoom mention format
        mention = zoom_user_identity.mention_format
        message = "{}\nInviting {} to look at the alert group.".format(
            templated_alert.title, mention
        )
    except ObjectDoesNotExist:
        message = "{}\nTried to invite {} to look at the alert group. Unfortunately {} is not linked to Zoom.".format(
            templated_alert.title, user.username, user.username
        )
        _create_error_log_record(
            UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_ZOOM_USER_NOT_IN_ZOOM
        )

    # Send as a reply/thread message
    try:
        client = ZoomClient()
        # For Zoom, we send a new message mentioning the user
        # Zoom doesn't have traditional threading like Slack, so we mention the original message context
        client.send_channel_message(
            channel_id=zoom_channel.channel_id,
            message=message,
            is_markdown=True,
        )
    except ZoomAPITokenInvalid:
        logger.error(f"Zoom API token is invalid. Could not notify user for alert {alert_group_pk}")
        _create_error_log_record(UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_ZOOM_API_TOKEN_INVALID)
    except ZoomAPIException as ex:
        logger.error(f"Zoom API error: {ex}")
        if ex.status != status.HTTP_401_UNAUTHORIZED:
            raise ex
        _create_error_log_record(UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_ZOOM_API_UNAUTHORIZED)
    else:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_zoom_message_async(alert_group_pk):
    """
    Update an existing Zoom message for an alert group.
    """
    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} not found")
        return

    try:
        zoom_message = alert_group.zoom_messages.get(message_type=ZoomMessage.ALERT_GROUP_MESSAGE)
    except ZoomMessage.DoesNotExist:
        logger.warning(f"Zoom message not found for alert group {alert_group_pk}")
        return

    # Render the updated message
    renderer = ZoomMessageRenderer(alert_group)
    interactive_cards = renderer.render_alert_group_message()

    try:
        client = ZoomClient()
        client.update_message(
            message_id=zoom_message.message_id,
            channel_id=zoom_message.channel_id,
            message="",
            interactive_cards=interactive_cards,
        )
        logger.info(f"Updated Zoom message {zoom_message.message_id} for alert group {alert_group_pk}")
    except ZoomAPITokenInvalid:
        logger.error(f"Zoom API token is invalid. Could not update message for alert group {alert_group_pk}")
    except ZoomAPIException as ex:
        logger.error(f"Zoom API error while updating message: {ex}")
        if ex.status not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]:
            raise ex
