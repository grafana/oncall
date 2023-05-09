import logging

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import ApiTokenAuthentication
from apps.phone_notifications.exceptions import (
    CallsLimitExceeded,
    FailedToMakeCall,
    FailedToSendSMS,
    NumberNotVerified,
    SMSLimitExceeded,
)
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.public_api.throttlers.phone_notification_throttler import PhoneNotificationThrottler

logger = logging.getLogger(__name__)


class PhoneNotificationDataSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField(max_length=1024)


class MakeCallView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [
        PhoneNotificationThrottler,
    ]

    def post(self, request):
        serializer = PhoneNotificationDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data = {}
        organization = self.request.auth.organization
        logger.info(f"Making cloud call. Email {serializer.validated_data['email']}")
        user = organization.users.filter(email=serializer.validated_data["email"]).first()
        if user is None:
            response_data = {"error": "user-not-found"}
            return Response(status=status.HTTP_404_NOT_FOUND, data=response_data)

        phone_backend = PhoneBackend()
        try:
            phone_backend.relay_oss_call(user, serializer.validated_data["message"])
        except FailedToMakeCall:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={"error": "failed"})
        except CallsLimitExceeded:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "limit-exceeded"})
        except NumberNotVerified:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "number-not-verified"})

        return Response(status=status.HTTP_200_OK, data=response_data)


class SendSMSView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [
        PhoneNotificationThrottler,
    ]

    def post(self, request):
        serializer = PhoneNotificationDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data = {}
        organization = self.request.auth.organization
        logger.info(f"Sending cloud sms. Email {serializer.validated_data['email']}")
        user = organization.users.filter(
            email=serializer.validated_data["email"], _verified_phone_number__isnull=False
        ).first()
        if user is None:
            response_data = {"error": "user-not-found"}
            return Response(status=status.HTTP_404_NOT_FOUND, data=response_data)

        phone_backend = PhoneBackend()
        try:
            phone_backend.relay_oss_sms(user, serializer.validated_data["message"])
        except FailedToSendSMS:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={"error": "failed"})
        except SMSLimitExceeded:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "limit-exceeded"})
        except NumberNotVerified:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "number-not-verified"})

        return Response(status=status.HTTP_200_OK, data=response_data)
