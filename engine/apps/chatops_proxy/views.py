from rest_framework.response import Response
from rest_framework.views import APIView

from apps.slack.installation import install_slack_integration
from apps.user_management.models import Organization, User

INTEGRATION_INSTALLED_EVENT_TYPE = "integration_installed"
INTEGRATION_UNINSTALLED_EVENT_TYPE = "integration_uninstalled"

PROVIDER_TYPE_SLACK = "slack"


class SlackInstallationHandler:
    @classmethod
    def match(cls, data):
        return (
            data.get("event_type") == INTEGRATION_INSTALLED_EVENT_TYPE
            and data.get("provider_type") == PROVIDER_TYPE_SLACK
        )

    @classmethod
    def handle(cls, data):
        stack_id = data.get("stack_id")
        user_id = data.get("grafana_user_id")
        payload = data.get("payload")
        print(f"Slack installation event received for stack {stack_id} and user {user_id}")

        org = Organization.objects.get(stack_id=stack_id)
        user = User.objects.get(user_id=user_id)
        install_slack_integration(org, user, payload)


class ChatopsEvents(APIView):
    HANDLERS = [SlackInstallationHandler]

    def post(self, request):
        for h in self.HANDLERS:
            if h.match(request.data):
                h.handle(request.data)
                break

        return Response(status=200)
