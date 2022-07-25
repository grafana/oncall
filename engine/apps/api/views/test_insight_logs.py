import logging

from django.apps import apps
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication

insight_logger = logging.getLogger("insight_logger")


class TestInsightLogsAPIView(APIView):
    """
    TestInsightLogsAPIView is used to test insight-logs infra setup.
    It will be removed once proper insight-logs will be instrumented.
    """

    authentication_classes = (PluginAuthentication,)

    def post(self, request):
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        org_id_to_enable_insight_logs, _ = DynamicSetting.objects.get_or_create(
            name="org_id_to_enable_insight_logs",
            defaults={"json_value": []},
        )
        org = self.request.user.organization
        insight_logs_enabled = org.id in org_id_to_enable_insight_logs.json_value
        if insight_logs_enabled:
            message = request.data.get("message", "hello world")
            insight_logger.info(f"tenant_id={self.request.user.organization.stack_id} message={message}")
            return Response()
        return Response(status=418)
