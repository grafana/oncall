import logging

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.base.exceptions import TwilioRestException

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.throttlers.phone_notification_throttler import PhoneNotificationThrottler
from apps.twilioapp.models import PhoneCall, SMSMessage

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
        user = organization.users.filter(
            email=serializer.validated_data["email"], _verified_phone_number__isnull=False
        ).first()
        if user is None:
            response_data = {"error": "user-not-found"}
            return Response(status=status.HTTP_404_NOT_FOUND, data=response_data)

        try:
            PhoneCall.make_grafana_cloud_call(user, serializer.validated_data["message"])
        except TwilioRestException as e:
            logger.info(f"Making cloud call. Twilio exception {str(e)}")
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data=response_data)
        except PhoneCall.PhoneCallsLimitExceeded:
            logger.info(f"Making cloud call. PhoneCallsLimitExceeded")
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "limit-exceeded"})

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

        try:
            SMSMessage.send_grafana_cloud_sms(user, serializer.validated_data["message"])
        except TwilioRestException as e:
            logger.info(f"Sending cloud sms. Twilio exception {str(e)}")
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data=response_data)
        except SMSMessage.SMSLimitExceeded:
            logger.info(f"Sending cloud sms. PhoneCallsLimitExceeded")
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "limit-exceeded"})

        return Response(status=status.HTTP_200_OK, data=response_data)
