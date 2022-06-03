# TODO: move to serializers
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.base.exceptions import TwilioRestException

from apps.auth_token.auth import ApiTokenAuthentication
from apps.twilioapp.models import PhoneCall, SMSMessage


class PhoneNotificationDataSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField(max_length=200)


class MakeCallView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # TODO: add ratelimit

    def post(self, request):
        # TODO: Grafana Twilio:
        # 1. Validate user's email
        # 2. Validate payload: clean_markup, escape_for_twilio_phone_call
        # 3. Create LogRecord (User notification policy or implement new one)
        serializer = PhoneNotificationDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = self.request.auth.organization
        # TODO: filter by verified phone number?
        user = organization.users.filter(email=serializer.validated_data["email"]).first()
        if not user or not user.verified_phone_number:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            PhoneCall.make_grafana_cloud_call(user, serializer.validated_data["message"])
        except TwilioRestException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PhoneCall.PhoneCallsLimitExceeded:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class SendSMSView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PhoneNotificationDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = self.request.auth.organization
        # TODO: filter by verified phone number?
        user = organization.users.filter(email=serializer.validated_data["email"]).first()
        if not user or not user.verified_phone_number:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            SMSMessage.send_cloud_sms(user, serializer.validated_data["message"])
        except TwilioRestException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except SMSMessage.SMSLimitExceeded:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
