from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import delete_alert_group, wipe
from apps.api.label_filtering import parse_label_query
from apps.api.permissions import RBACPermission
from apps.auth_token.auth import ApiTokenAuthentication, GrafanaServiceAccountAuthentication
from apps.public_api.constants import VALID_DATE_FOR_DELETE_INCIDENT
from apps.public_api.helpers import is_valid_group_creation_date, team_has_slack_token_for_deleting
from apps.public_api.serializers import AlertGroupSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.exceptions import BadRequest, Forbidden
from common.api_helpers.filters import (
    NO_TEAM_VALUE,
    ByTeamModelFieldFilterMixin,
    DateRangeFilterMixin,
    get_team_queryset,
)
from common.api_helpers.mixins import AlertGroupEnrichingMixin, RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class AlertGroupFilters(ByTeamModelFieldFilterMixin, DateRangeFilterMixin, filters.FilterSet):
    # query field param name to filter by team
    TEAM_FILTER_FIELD_NAME = "team_id"

    id = filters.CharFilter(field_name="public_primary_key")

    team_id = filters.ModelChoiceFilter(
        field_name="channel__team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value=NO_TEAM_VALUE,
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_single_value.__name__,
    )

    started_at = filters.CharFilter(
        field_name="started_at",
        method=DateRangeFilterMixin.filter_date_range.__name__,
    )


class AlertGroupView(
    AlertGroupEnrichingMixin,
    RateLimitHeadersMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    authentication_classes = (GrafanaServiceAccountAuthentication, ApiTokenAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "list": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "retrieve": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "destroy": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "acknowledge": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unacknowledge": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "resolve": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unresolve": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "silence": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unsilence": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    throttle_classes = [UserThrottle]

    model = AlertGroup
    serializer_class = AlertGroupSerializer
    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AlertGroupFilters

    def get_queryset(self):
        # no select_related or prefetch_related is used at this point, it will be done on paginate_queryset.

        route_id = self.request.query_params.get("route_id", None)
        integration_id = self.request.query_params.get("integration_id", None)
        state = self.request.query_params.get("state", None)

        alert_receive_channels_qs = AlertReceiveChannel.objects_with_deleted.filter(
            organization_id=self.request.auth.organization.id
        )
        if integration_id:
            alert_receive_channels_qs = alert_receive_channels_qs.filter(public_primary_key=integration_id)

        alert_receive_channels_ids = list(alert_receive_channels_qs.values_list("id", flat=True))
        queryset = AlertGroup.objects.filter(channel__in=alert_receive_channels_ids).order_by("-started_at")

        if route_id:
            queryset = queryset.filter(channel_filter__public_primary_key=route_id)
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

        # filter by alert group (static, applied) labels
        label_query = self.request.query_params.getlist("label", [])
        kv_pairs = parse_label_query(label_query)
        for key, value in kv_pairs:
            queryset = queryset.filter(
                labels__organization=self.request.auth.organization,
                labels__key_name=key,
                labels__value_name=value,
            )

        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            obj = AlertGroup.objects.filter(
                channel__organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
            obj = self.enrich([obj])[0]
            return obj
        except AlertGroup.DoesNotExist:
            raise NotFound

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(request.data, dict):
            return Response(data="A dict with a `mode` key is expected", status=status.HTTP_400_BAD_REQUEST)
        mode = request.data.get("mode", "wipe")
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
        elif mode == "wipe":
            wipe.apply_async((instance.pk, request.user.pk))
        else:
            return Response(data="Invalid mode", status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to acknowledge alert groups")

        alert_group = self.get_object()

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't acknowledge an acknowledged alert group")

        if alert_group.resolved:
            raise BadRequest(detail="Can't acknowledge a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't acknowledge an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't acknowledge a maintenance alert group")

        alert_group.acknowledge_by_user_or_backsync(self.request.user, action_source=ActionSource.API)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to unacknowledge alert groups")

        alert_group = self.get_object()

        if not alert_group.acknowledged:
            raise BadRequest(detail="Can't unacknowledge an unacknowledged alert group")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unacknowledge a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't unacknowledge an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unacknowledge a maintenance alert group")

        alert_group.un_acknowledge_by_user_or_backsync(self.request.user, action_source=ActionSource.API)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def resolve(self, request, pk):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to resolve alert groups")

        alert_group = self.get_object()

        if alert_group.resolved:
            raise BadRequest(detail="Can't resolve a resolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't resolve an attached alert group")

        if alert_group.is_maintenance_incident:
            alert_group.stop_maintenance(self.request.user)
        else:
            alert_group.resolve_by_user_or_backsync(self.request.user, action_source=ActionSource.API)

        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unresolve(self, request, pk):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to unresolve alert groups")

        alert_group = self.get_object()

        if not alert_group.resolved:
            raise BadRequest(detail="Can't unresolve an unresolved alert group")

        if alert_group.root_alert_group:
            raise BadRequest(detail="Can't unresolve an attached alert group")

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unresolve a maintenance alert group")

        alert_group.un_resolve_by_user_or_backsync(self.request.user, action_source=ActionSource.API)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def silence(self, request, pk=None):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to silence alert groups")

        alert_group = self.get_object()

        delay = request.data.get("delay")
        if delay is None:
            raise BadRequest(detail="delay is required")
        try:
            delay = int(delay)
        except ValueError:
            raise BadRequest(detail="invalid delay value")
        if delay < -1:
            raise BadRequest(detail="invalid delay value")

        if alert_group.resolved:
            raise BadRequest(detail="Can't silence a resolved alert group")

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't silence an acknowledged alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't silence an attached alert group")

        alert_group.silence_by_user_or_backsync(request.user, silence_delay=delay, action_source=ActionSource.API)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unsilence(self, request, pk=None):
        if request.user.is_service_account:
            raise Forbidden(detail="Service accounts are not allowed to unsilence alert groups")

        alert_group = self.get_object()

        if not alert_group.silenced:
            raise BadRequest(detail="Can't unsilence an unsilenced alert group")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unsilence a resolved alert group")

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't unsilence an acknowledged alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unsilence an attached alert group")

        alert_group.un_silence_by_user_or_backsync(request.user, action_source=ActionSource.API)

        return Response(status=status.HTTP_200_OK)
