import logging

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatops_proxy.events import ChatopsEventsHandler
from apps.chatops_proxy.events.signature import verify_signature

logger = logging.getLogger(__name__)

handler = ChatopsEventsHandler()


class ChatopsEventsView(APIView):
    def post(self, request):
        verified = verify_signature(request, settings.CHATOPS_SIGNING_SECRET)
        if not verified:
            logger.error("ChatopsEventsView: Invalid signature")
            return Response(status=401)
        found = handler.handle(request.data)
        if not found:
            return Response(status=400)
        return Response(status=200)
