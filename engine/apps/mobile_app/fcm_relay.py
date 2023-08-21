import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import AndroidConfig, APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.auth_token.auth import ApiTokenAuthentication
from apps.mobile_app.models import FCMDevice
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)
task_logger.setLevel(logging.DEBUG)


class FCMRelayThrottler(UserRateThrottle):
    scope = "fcm_relay"
    rate = "300/m"


class FCMRelayView(APIView):
    """
    This view accepts push notifications from OSS instances and forwards these requests to FCM.
    Requests to this endpoint come from OSS instances: apps.mobile_app.tasks.send_push_notification_to_fcm_relay.
    The view uses public API authentication, so an OSS instance must be connected to cloud to use FCM relay.
    """

    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [FCMRelayThrottler]

    def post(self, request):
        if not settings.FCM_RELAY_ENABLED:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            token = request.data["token"]
            data = request.data["data"]
            apns = request.data["apns"]
            android = request.data.get("android")  # optional
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        fcm_relay_async.delay(token=token, data=data, apns=apns, android=android)
        return Response(status=status.HTTP_200_OK)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else 5
)
def fcm_relay_async(token, data, apns, android=None):
    message = _get_message_from_request_data(token, data, apns, android)

    # https://firebase.google.com/docs/cloud-messaging/http-server-ref#interpret-downstream
    response = FCMDevice(registration_id=token).send_message(message)
    task_logger.debug(f"FCM response: {response}")

    if isinstance(response, FirebaseError):
        raise response


def _get_message_from_request_data(token, data, apns, android):
    """
    Create Message object from JSON payload from OSS instance.
    """

    return Message(
        token=token, data=data, apns=_deserialize_apns(apns), android=AndroidConfig(**android) if android else None
    )


def _deserialize_apns(apns):
    """
    Create APNSConfig object from JSON payload from OSS instance.
    """
    aps = apns.get("payload", {}).get("aps", {})
    if not aps:
        return None

    thread_id = aps.get("thread-id")
    badge = aps.get("badge")

    alert = aps.get("alert")
    if isinstance(alert, dict):
        alert = ApsAlert(**alert)

    sound = aps.get("sound")
    if isinstance(sound, dict):
        sound = CriticalSound(**sound)

    # remove all keys from "aps" so it can be used for custom_data
    for key in ["thread-id", "badge", "alert", "sound"]:
        aps.pop(key, None)

    return APNSConfig(
        payload=APNSPayload(
            aps=Aps(
                thread_id=thread_id,
                badge=badge,
                alert=alert,
                sound=sound,
                custom_data=aps,
            )
        ),
        headers=apns.get("headers"),
    )
