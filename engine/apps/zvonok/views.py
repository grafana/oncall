from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.utils import live_settings

from .status_callback import update_zvonok_call_status


class AllowOnlyZvonok(BasePermission):
    def has_permission(self, request, view):
        call_id = request.GET.get(live_settings.ZVONOK_POSTBACK_CALL_ID)
        if not call_id:
            return False

        campaign_id = request.GET.get(live_settings.ZVONOK_POSTBACK_CAMPAIGN_ID)
        if not campaign_id:
            return False

        if campaign_id != live_settings.ZVONOK_CAMPAIGN_ID:
            return False
        from apps.zvonok.models import ZvonokPhoneCall

        call = ZvonokPhoneCall.objects.filter(call_id=call_id, campaign_id=campaign_id).first()
        if call:
            return self.validate_request(request)
        return False

    def validate_request(self, request):
        if request.GET.get(live_settings.ZVONOK_POSTBACK_STATUS):
            return True
        return False


# Receive Call Status from Zvonok
class CallStatusCallback(APIView):
    permission_classes = [AllowOnlyZvonok]

    def get(self, request):
        self._handle_call_status(request)
        return Response(data="", status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        self._handle_call_status(request)
        return Response(data="", status=status.HTTP_204_NO_CONTENT)

    def _handle_call_status(self, request):
        call_id = request.GET.get(live_settings.ZVONOK_POSTBACK_CALL_ID)
        call_status = request.GET.get(live_settings.ZVONOK_POSTBACK_STATUS)
        user_choice = request.GET.get(live_settings.ZVONOK_POSTBACK_USER_CHOICE)
        update_zvonok_call_status(call_id=call_id, call_status=call_status, user_choice=user_choice)
