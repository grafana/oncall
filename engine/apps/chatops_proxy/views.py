from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatops_proxy.events import ChatopsEventsHandler

handler = ChatopsEventsHandler()


class ChatopsEventsView(APIView):
    # TODO: check signature to verify requests
    def post(self, request):
        found = handler.handle(request.data)
        if not found:
            return Response(status=400)
        return Response(status=200)
