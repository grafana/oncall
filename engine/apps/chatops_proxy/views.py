from rest_framework.response import Response
from rest_framework.views import APIView


class ReceiveBroadcast(APIView):
    def post(self, request):
        print(request.data)
        return Response(status=200)
