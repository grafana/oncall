import logging

from fcm_django.models import FCMDevice
from firebase_admin.messaging import APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.auth_token.auth import ApiTokenAuthentication

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FCMRelayThrottler(UserRateThrottle):
    scope = "fcm_relay"
    rate = "60/m"


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
        try:
            token = request.data["token"]
            data = request.data["data"]
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        message = Message(token=token, data=data, apns=get_apns(request.data))

        logger.debug(f"Sending message to FCM: {message}")
        result = FCMDevice(registration_id=token).send_message(message)
        logger.debug(f"FCM response: {result}")

        return Response(status=status.HTTP_200_OK)


def get_apns(data):
    """
    Create APNSConfig object from JSON payload from OSS instance.
    """
    aps = data.get("apns", {}).get("payload", {}).get("aps", {})
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
        )
    )
