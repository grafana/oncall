from rest_framework.response import Response
from rest_framework.views import APIView

from apps.telegram.tasks import register_telegram_webhook
from apps.telegram.updates.update_manager import UpdateManager

register_telegram_webhook.delay()


class WebHookView(APIView):
    def get(self, request, format=None):
        return Response("hello")

    def post(self, request):
        UpdateManager.process_request(request)
        return Response(status=200)
