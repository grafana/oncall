from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup
from apps.alerts.tasks import delete_alert_group, wipe
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.constants import VALID_DATE_FOR_DELETE_INCIDENT
from apps.public_api.helpers import is_valid_group_creation_date, team_has_slack_token_for_deleting
from apps.public_api.serializers import IncidentSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, get_team_queryset
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class IncidentByTeamFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    team = filters.ModelChoiceFilter(
        field_name="channel__team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value="null",
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_single_value.__name__,
    )

    id = filters.CharFilter(field_name="public_primary_key")


class IncidentView(RateLimitHeadersMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = AlertGroup
    serializer_class = IncidentSerializer
    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IncidentByTeamFilter

    def get_queryset(self):
        route_id = self.request.query_params.get("route_id", None)
        integration_id = self.request.query_params.get("integration_id", None)
        state = self.request.query_params.get("state", None)

        queryset = AlertGroup.objects.filter(
            channel__organization=self.request.auth.organization,
        ).order_by("-started_at")

        if route_id:
            queryset = queryset.filter(channel_filter__public_primary_key=route_id)
        if integration_id:
            queryset = queryset.filter(channel__public_primary_key=integration_id)
        if state:
            choices = dict(AlertGroup.STATUS_CHOICES)
            try:
                choice = [i for i in choices if choices[i] == state.lower().capitalize()][0]
                status_filter = Q()
                if choice == AlertGroup.NEW:
                    status_filter = AlertGroup.get_new_state_filter()
                elif choice == AlertGroup.SILENCED:
                    status_filter = AlertGroup.get_silenced_state_filter()
                elif choice == AlertGroup.ACKNOWLEDGED:
                    status_filter = AlertGroup.get_acknowledged_state_filter()
                elif choice == AlertGroup.RESOLVED:
                    status_filter = AlertGroup.get_resolved_state_filter()
                queryset = queryset.filter(status_filter)
            except IndexError:
                valid_choices_text = ", ".join(
                    [status_choice[1].lower() for status_choice in AlertGroup.STATUS_CHOICES]
                )
                raise BadRequest(detail={"state": f"Must be one of the following: {valid_choices_text}"})

        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return AlertGroup.objects.filter(
                channel__organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
        except AlertGroup.DoesNotExist:
            raise NotFound

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(request.data, dict):
            return Response(data="A dict with a `mode` key is expected", status=status.HTTP_400_BAD_REQUEST)
        mode = request.data.get("mode")
        if mode == "delete":
            if not team_has_slack_token_for_deleting(instance):
                raise BadRequest(
                    detail="Your OnCall Bot in Slack is outdated. Please reinstall OnCall Bot and try again."
                )
            elif not is_valid_group_creation_date(instance):
                raise BadRequest(
                    detail=f"We are unable to “delete” old alert_groups (created before "
                    f"{VALID_DATE_FOR_DELETE_INCIDENT.strftime('%d %B %Y')}) using API. "
                    f"Please use “wipe” mode or contact help. Sorry for that!"
                )
            else:
                delete_alert_group.apply_async((instance.pk, request.user.pk))
        else:
            wipe.apply_async((instance.pk, request.user.pk))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        alert_group = self.get_object()

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't acknowledge an acknowledged alert group")

        if alert_group.resolved:
            raise BadRequest(detail="Can't acknowledge a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't acknowledge an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't acknowledge a maintenance alert group")

        alert_group.acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        alert_group = self.get_object()

        if not alert_group.acknowledged:
            raise BadRequest(detail="Can't unacknowledge an unacknowledged alert group")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unacknowledge a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't unacknowledge an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unacknowledge a maintenance alert group")

        alert_group.un_acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def resolve(self, request, pk):
        alert_group = self.get_object()

        if alert_group.resolved:
            raise BadRequest(detail="Can't resolve a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't resolve an attached alert group")

        if alert_group.is_maintenance_incident:
            alert_group.stop_maintenance(self.request.user)
        else:
            alert_group.resolve_by_user(self.request.user, action_source=ActionSource.WEB)

        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unresolve(self, request, pk):
        alert_group = self.get_object()

        if not alert_group.resolved:
            raise BadRequest(detail="Can't unresolve an unresolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't unresolve an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unresolve a maintenance alert group")

        alert_group.un_resolve_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(status=status.HTTP_200_OK)
