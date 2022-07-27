import logging

from django.apps import apps
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.request_validator import RequestValidator

from apps.base.utils import live_settings
from apps.twilioapp.utils import process_call_data
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class AllowOnlyTwilio(BasePermission):
    def has_permission(self, request, view):
        # https://www.twilio.com/docs/usage/tutorials/how-to-secure-your-django-project-by-validating-incoming-twilio-requests
        # https://www.django-rest-framework.org/api-guide/permissions/
        validator = RequestValidator(live_settings.TWILIO_AUTH_TOKEN)
        location = create_engine_url(request.get_full_path())
        request_valid = validator.validate(
            request.build_absolute_uri(location=location), request.POST, request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
        )
        return request_valid


class HealthCheckView(APIView):
    def get(self, request):
        return Response("OK")


class GatherView(APIView):
    permission_classes = [AllowOnlyTwilio]

    def post(self, request):
        digit = request.POST.get("Digits")
        call_sid = request.POST.get("CallSid")

        logging.info(f"For CallSid: {call_sid} pressed digit: {digit}")

        response = process_call_data(call_sid=call_sid, digit=digit)

        return HttpResponse(str(response), content_type="application/xml; charset=utf-8")


# Receive SMS Status Update from Twilio
class SMSStatusCallback(APIView):
    permission_classes = [AllowOnlyTwilio]

    def post(self, request):
        message_sid = request.POST.get("MessageSid")
        message_status = request.POST.get("MessageStatus")
        logging.info(f"SID: {message_sid}, Status: {message_status}")

        SMSMessage = apps.get_model("twilioapp", "SMSMessage")
        SMSMessage.objects.update_status(message_sid=message_sid, message_status=message_status)
        return Response(data="", status=status.HTTP_204_NO_CONTENT)


# Receive Call Status Update from Twilio
class CallStatusCallback(APIView):
    permission_classes = [AllowOnlyTwilio]

    def post(self, request):
        call_sid = request.POST.get("CallSid")
        call_status = request.POST.get("CallStatus")

        logging.info(f"SID: {call_sid}, Status: {call_status}")

        PhoneCall = apps.get_model("twilioapp", "PhoneCall")
        PhoneCall.objects.update_status(call_sid=call_sid, call_status=call_status)

        return Response(data="", status=status.HTTP_204_NO_CONTENT)
