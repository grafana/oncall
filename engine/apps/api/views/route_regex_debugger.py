import json
import re

from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.incident_appearance.renderers.web_renderer import AlertWebRenderer
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest


class RouteRegexDebuggerView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        organization = self.request.auth.organization
        team = self.request.user.current_team

        regex = request.query_params.get("regex", None)
        alert_receive_channel_id = request.query_params.get("alert_receive_channel_id", None)

        if regex is None:
            raise BadRequest(detail={"regex": ["This field is required."]})
        if regex == "":
            return Response([])
        try:
            re.compile(regex)
        except re.error:
            raise BadRequest(detail={"regex": ["Invalid regex."]})

        qs = AlertReceiveChannel.objects.filter(
            organization_id=organization,
            team_id=team,
        )

        # if alert_receive_channel_id is not set return result for all the alert receive channels
        if alert_receive_channel_id is not None:
            qs.get(public_primary_key=alert_receive_channel_id)

        alert_receive_channels_ids = list(qs.values_list("id", flat=True))

        incidents_matching_regex = []
        MAX_INCIDENTS_TO_SHOW = 5
        INCIDENTS_TO_LOOKUP = 100
        for ag in (
            AlertGroup.unarchived_objects.prefetch_related(Prefetch("alerts", queryset=Alert.objects.order_by("pk")))
            .filter(channel_id__in=alert_receive_channels_ids)
            .order_by("-started_at")[:INCIDENTS_TO_LOOKUP]
        ):

            if len(incidents_matching_regex) < MAX_INCIDENTS_TO_SHOW:
                first_alert = ag.alerts.all()[0]
                if re.search(regex, json.dumps(first_alert.raw_request_data)):
                    title = AlertWebRenderer(first_alert).render()["title"]
                    incidents_matching_regex.append(
                        {
                            "title": title,
                            "pk": ag.public_primary_key,
                            "payload": first_alert.raw_request_data,
                            "inside_organization_number": ag.inside_organization_number,
                        }
                    )

        return Response(incidents_matching_regex)
