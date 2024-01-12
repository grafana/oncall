import json
import logging
import typing

import requests
from django.conf import settings
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import AndroidConfig, APNSConfig, APNSPayload, Message, UnregisteredError
from requests import HTTPError
from rest_framework import status

from apps.base.utils import live_settings
from apps.mobile_app.types import FCMMessageData, MessageType
from common.api_helpers.utils import create_engine_url

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice
    from apps.user_management.models import Organization


MAX_RETRIES = 1 if settings.DEBUG else 10

# UnregisteredError
# App instance was unregistered from FCM. This usually means that the token used is no longer valid and a
# new one must be used.
#
# In other words, this error occurs outside of our control and retrying will never fix it, therefore we should skip
FIREBASE_ERRORS_TO_NOT_RETRY = (UnregisteredError,)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _send_push_notification_to_fcm_relay(message: Message) -> requests.Response:
    """
    Send push notification to FCM relay on cloud instance: apps.mobile_app.fcm_relay.FCMRelayView
    """
    url = create_engine_url("mobile_app/v1/fcm_relay", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)

    response = requests.post(
        url, headers={"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}, json=json.loads(str(message))
    )
    response.raise_for_status()

    return response


def send_message_to_fcm_device(device: "FCMDevice", message: Message) -> bool:
    """
    https://firebase.google.com/docs/cloud-messaging/http-server-ref#interpret-downstream
    """
    response = device.send_message(message)
    logger.debug(f"FCM response: {response}")

    if isinstance(response, FirebaseError):
        logger.exception(
            f"FCM error occured in mobile_app.utils.send_message_to_fcm_device fcm_device_info={device} "
            f"firebase_error_code={response._code} firebase_error_cause={response._cause} "
            f"firebase_error_http_response={response._http_response}"
        )

        if isinstance(response, FIREBASE_ERRORS_TO_NOT_RETRY):
            logger.warning(f"FCM error {response} is not being retried as we explicitly do not want to retry it")
            return False

        raise response
    return True


def send_push_notification(
    device_to_notify: "FCMDevice", message: Message, error_cb: typing.Optional[typing.Callable[..., None]] = None
) -> bool:
    logger.debug(f"Sending push notification to device type {device_to_notify.type} with message: {message}")

    def _error_cb():
        if error_cb:
            error_cb()

    if settings.IS_OPEN_SOURCE:
        # FCM relay uses cloud connection to send push notifications
        from apps.oss_installation.models import CloudConnector

        if not CloudConnector.objects.exists():
            _error_cb()
            logger.error("Error while sending a mobile push notification: not connected to cloud")
            return False

        try:
            response = _send_push_notification_to_fcm_relay(message)
            logger.debug(f"FCM relay response: {response}")
        except HTTPError as e:
            if status.HTTP_400_BAD_REQUEST <= e.response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
                # do not retry on HTTP client errors (4xx errors)
                _error_cb()
                logger.error(
                    f"Error while sending a mobile push notification: HTTP client error {e.response.status_code}"
                )
                return False
            else:
                raise
    else:
        succeeded = send_message_to_fcm_device(device_to_notify, message)
        if not succeeded:
            _error_cb()
            return False

    # notification succeeded (otherwise raised exception before)
    return True


def construct_fcm_message(
    message_type: MessageType,
    device_to_notify: "FCMDevice",
    thread_id: str,
    data: FCMMessageData,
    apns_payload: typing.Optional[APNSPayload] = None,
) -> Message:
    apns_config_kwargs = {}

    if apns_payload is not None:
        apns_config_kwargs["payload"] = apns_payload

    return Message(
        token=device_to_notify.registration_id,
        data={
            # from the docs..
            # A dictionary of data fields (optional). All keys and values in the dictionary must be strings
            **data,
            "type": message_type,
            "thread_id": thread_id,
        },
        android=AndroidConfig(
            # from the docs
            # https://firebase.google.com/docs/cloud-messaging/concept-options#setting-the-priority-of-a-message
            #
            # Normal priority.
            # Normal priority messages are delivered immediately when the app is in the foreground.
            # For backgrounded apps, delivery may be delayed. For less time-sensitive messages, such as notifications
            # of new email, keeping your UI in sync, or syncing app data in the background, choose normal delivery
            # priority.
            #
            # High priority.
            # FCM attempts to deliver high priority messages immediately even if the device is in Doze mode.
            # High priority messages are for time-sensitive, user visible content.
            priority="high",
        ),
        apns=APNSConfig(
            **apns_config_kwargs,
            headers={
                # From the docs
                # https://firebase.google.com/docs/cloud-messaging/concept-options#setting-the-priority-of-a-message
                "apns-priority": "10",
            },
        ),
    )


def add_stack_slug_to_message_title(title: str, organization: "Organization") -> str:
    return f"[{organization.stack_slug}] {title}"
