from django.conf import settings
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.views import APIView

from common.oncall_gateway.client import ChatopsProxyAPIClient


class OauthStartView(APIView):
    def get(self, request):
        client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)

        try:
            link, _ = client.get_slack_oauth_link(
                request.auth.organization.stack_id, request.auth.user.user_id, request.auth.organization.web_link
            )
            return redirect(link)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
