from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatops_proxy.events import ChatopsEventsHandler

handler = ChatopsEventsHandler()


class ChatopsEventsView(APIView):
    # TODO: check signature
    def post(self, request):
        handler.handle(request.data)
        return Response(status=200)
