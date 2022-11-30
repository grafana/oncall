from push_notifications.gcm import send_message
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

REQUIRED_FIELDS = {"registration_ids", "notification", "data"}


class FCMRelayView(APIView):
    def post(self, request):
        # make sure every field in REQUIRED_FIELDS is present in request payload
        if not REQUIRED_FIELDS.issubset(request.data.keys()):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        registration_ids = request.data["registration_ids"]
        data = {
            **request.data["data"],
            **request.data["notification"],
        }

        return send_message(registration_ids=registration_ids, data=data, cloud_type="FCM", application_id=None)
