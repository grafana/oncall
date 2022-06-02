import logging

from django.apps import apps
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sendgridapp.permissions import AllowOnlySendgrid

logger = logging.getLogger(__name__)


# Receive Email Status Update from Sendgrid
class EmailStatusCallback(APIView):
    # https://sendgrid.com/docs/for-developers/tracking-events/event/#delivery-events
    permission_classes = [AllowOnlySendgrid]

    def post(self, request):
        for data in request.data:
            message_uuid = data.get("message_uuid")
            message_status = data.get("event")
            if message_status is not None and "type" in message_status:
                message_status = message_status["type"]
            logger.info(f"UUID: {message_uuid}, Status: {message_status}")

            EmailMessage = apps.get_model("sendgridapp", "EmailMessage")
            EmailMessage.objects.update_status(message_uuid=message_uuid, message_status=message_status)

        return Response(data="", status=status.HTTP_204_NO_CONTENT)
