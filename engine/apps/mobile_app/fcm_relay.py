from push_notifications.gcm import send_message
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

REQUIRED_FIELDS = {"registration_ids", "notification", "data"}


class FCMRelayView(APIView):
    def post(self, request):
        """
        This view accepts requests from OSS instances of Grafana OnCall and forwards these requests to FCM.
        Requests will be sent with the FCM_API_KEY configured in server settings
        (see PUSH_NOTIFICATIONS_SETTINGS in settings/base.py)
        """

        if not REQUIRED_FIELDS.issubset(request.data.keys()):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        registration_ids = request.data["registration_ids"]
        data = {
            **request.data["data"],
            **request.data["notification"],
        }

        return send_message(registration_ids=registration_ids, data=data, cloud_type="FCM")
