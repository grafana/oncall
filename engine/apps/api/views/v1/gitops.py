from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.terraform_renderer import TerraformFileRenderer, TerraformStateRenderer
from apps.api.response_renderers import PlainTextRenderer
from apps.auth_token.auth import PluginAuthentication


class TerraformGitOpsView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    renderer_classes = [PlainTextRenderer]

    def get(self, request):
        organization = self.request.auth.organization
        renderer = TerraformFileRenderer(organization)
        terraform_file = renderer.render_terraform_file()
        return Response(terraform_file)


class TerraformStateView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    renderer_classes = (PlainTextRenderer,)

    def get(self, request):
        organization = self.request.auth.organization
        renderer = TerraformStateRenderer(organization)
        terraform_state = renderer.render_state()
        return Response(terraform_state)
