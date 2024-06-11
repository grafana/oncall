from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .status_callback import update_exotel_call_status


class AllowOnlyExotel(BasePermission):
    def has_permission(self, request, view):
        call_id = request.data.get("CallSid")
        if not call_id:
            return False

        status = request.data.get("Status")
        if not status:
            return False

        from apps.exotel.models import ExotelPhoneCall

        call = ExotelPhoneCall.objects.filter(call_id=call_id).first()
        if call:
            return self.validate_request(request)
        return False

    def validate_request(self, request):
        # No reliable way to validate an exotel status callback as of now
        # this is confirmed by exotel customer support too
        # It is better to allow only exotel server IPs to this endpoint through firewall or similar means
        if request.META.get("HTTP_USER_AGENT") == "Exotel Servers":
            return True
        return False


# Receive Call Status from Exotel
class CallStatusCallback(APIView):
    permission_classes = [AllowOnlyExotel]

    def post(self, request):
        self._handle_call_status(request)
        return Response(data="", status=status.HTTP_204_NO_CONTENT)

    def _handle_call_status(self, request):
        call_id = request.data.get("CallSid")
        call_status = request.data.get("Status")
        update_exotel_call_status(call_id=call_id, call_status=call_status)
