from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel
from apps.alerts.models.maintainable_object import MaintainableObject
from apps.api.permissions import RBACPermission
from apps.api.serializers.alert_receive_channel import (
    AlertReceiveChannelSerializer,
    AlertReceiveChannelUpdateSerializer,
    FilterAlertReceiveChannelSerializer,
)
from apps.api.throttlers import DemoAlertThrottler
from apps.auth_token.auth import PluginAuthentication
from apps.integrations.legacy_prefix import has_legacy_prefix, remove_legacy_prefix
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import (
    FilterSerializerMixin,
    PreviewTemplateException,
    PreviewTemplateMixin,
    PublicPrimaryKeyMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.paginators import FifteenPageSizePaginator
from common.exceptions import MaintenanceCouldNotBeStartedError, TeamCanNotBeChangedError, UnableToSendDemoAlert
from common.insight_log import EntityEvent, write_resource_insight_log


class AlertReceiveChannelFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    maintenance_mode = filters.MultipleChoiceFilter(
        choices=AlertReceiveChannel.MAINTENANCE_MODE_CHOICES, method="filter_maintenance_mode"
    )
    integration = filters.MultipleChoiceFilter(choices=AlertReceiveChannel.INTEGRATION_CHOICES)
    team = TeamModelMultipleChoiceFilter()

    class Meta:
        model = AlertReceiveChannel
        fields = ["integration", "maintenance_mode", "team"]

    def filter_maintenance_mode(self, queryset, name, value):
        q_objects = Q()
        if not value:
            return queryset
        for mode in value:
            try:
                mode = int(mode)
            except (ValueError, TypeError):
                raise BadRequest(detail="Invalid mode value")
            if mode not in [AlertReceiveChannel.DEBUG_MAINTENANCE, AlertReceiveChannel.MAINTENANCE]:
                raise BadRequest(detail="Invalid mode value")
            q_objects |= Q(maintenance_mode=mode)

        queryset = queryset.filter(q_objects)

        return queryset


class AlertReceiveChannelView(
    PreviewTemplateMixin,
    TeamFilteringMixin,
    PublicPrimaryKeyMixin,
    FilterSerializerMixin,
    UpdateSerializerMixin,
    ModelViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    model = AlertReceiveChannel
    serializer_class = AlertReceiveChannelSerializer
    filter_serializer_class = FilterAlertReceiveChannelSerializer
    update_serializer_class = AlertReceiveChannelUpdateSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ("verbal_name",)

    filterset_class = AlertReceiveChannelFilter
    pagination_class = FifteenPageSizePaginator

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "list": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "retrieve": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "integration_options": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "counters": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "counters_per_integration": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "send_demo_alert": [RBACPermission.Permissions.INTEGRATIONS_TEST],
        "preview_template": [RBACPermission.Permissions.INTEGRATIONS_TEST],
        "create": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "partial_update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "destroy": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "change_team": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "filters": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "start_maintenance": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "stop_maintenance": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "validate_name": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "migrate": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "connected_contact_points": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "contact_points": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "connect_contact_point": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "create_contact_point": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "disconnect_contact_point": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
    }

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    def get_queryset(self, eager=True, ignore_filtering_by_available_teams=False):
        is_filters_request = self.request.query_params.get("filters", "false") == "true"
        organization = self.request.auth.organization
        if is_filters_request:
            queryset = AlertReceiveChannel.objects_with_maintenance.filter(
                organization=organization,
            )
        else:
            queryset = AlertReceiveChannel.objects.filter(
                organization=organization,
            )
            if eager:
                queryset = self.serializer_class.setup_eager_loading(queryset)

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        return queryset

    def paginate_queryset(self, queryset):
        """
        If `skip_pagination` is provided and is equal to "true" (or "True"), it will return
        a non paginated list of results. This is useful for Grafana Alerting
        """
        if self.request.query_params.get("skip_pagination", "false").lower() == "true":
            return None
        return super().paginate_queryset(queryset)

    @action(detail=True, methods=["post"], throttle_classes=[DemoAlertThrottler])
    def send_demo_alert(self, request, pk):
        instance = self.get_object()
        payload = request.data.get("demo_alert_payload", None)

        if payload is not None and not isinstance(payload, dict):
            raise BadRequest(detail="Payload for demo alert must be a valid json object")

        try:
            instance.send_demo_alert(payload=payload)
        except UnableToSendDemoAlert as e:
            raise BadRequest(detail=str(e))

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def integration_options(self, request):
        choices = []
        featured_choices = []
        for integration_id, integration_title in AlertReceiveChannel.INTEGRATION_CHOICES:
            if integration_id in AlertReceiveChannel.WEB_INTEGRATION_CHOICES:
                choice = {
                    "value": integration_id,
                    "display_name": integration_title,
                    "short_description": AlertReceiveChannel.INTEGRATION_SHORT_DESCRIPTION[integration_id],
                    "featured": integration_id in AlertReceiveChannel.INTEGRATION_FEATURED,
                    "featured_tag_name": AlertReceiveChannel.INTEGRATION_FEATURED_TAG_NAME[integration_id]
                    if integration_id in AlertReceiveChannel.INTEGRATION_FEATURED_TAG_NAME
                    else None,
                }
                # if integration is featured we show it in the beginning
                if choice["featured"]:
                    featured_choices.append(choice)
                else:
                    choices.append(choice)
        return Response(featured_choices + choices)

    @action(detail=True, methods=["put"])
    def change_team(self, request, pk):
        instance = self.get_object()

        if "team_id" not in request.query_params:
            raise BadRequest(detail="team_id must be specified")

        team_id = request.query_params["team_id"]
        if team_id == "null":
            team_id = None

        try:
            instance.change_team(team_id=team_id, user=self.request.user)
        except TeamCanNotBeChangedError as e:
            raise BadRequest(detail=e)

        return Response()

    @action(methods=["get"], detail=False)
    def counters(self, request):
        queryset = self.filter_queryset(self.get_queryset(eager=False))
        response = {}
        for alert_receive_channel in queryset:
            response[alert_receive_channel.public_primary_key] = {
                "alerts_count": alert_receive_channel.alerts_count,
                "alert_groups_count": alert_receive_channel.alert_groups_count,
            }
        return Response(response)

    @action(methods=["get"], detail=True, url_path="counters")
    def counters_per_integration(self, request, pk):
        alert_receive_channel = self.get_object()
        response = {
            alert_receive_channel.public_primary_key: {
                "alerts_count": alert_receive_channel.alerts_count,
                "alert_groups_count": alert_receive_channel.alert_groups_count,
            }
        }
        return Response(response)

    # This method is required for PreviewTemplateMixin
    def get_alert_to_template(self, payload=None):
        channel = self.get_object()

        try:
            if payload is None:
                return channel.alert_groups.last().alerts.first()
            else:
                if type(payload) != dict:
                    raise PreviewTemplateException("Payload must be a valid json object")
                # Build Alert and AlertGroup objects to pass to templater without saving them to db
                alert_group_to_template = AlertGroup(channel=channel)
                return Alert(raw_request_data=payload, group=alert_group_to_template)
        except AttributeError:
            return None

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
            {
                "name": "integration",
                "display_name": "Type",
                "type": "options",
                "href": api_root + "alert_receive_channels/integration_options/",
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)

    @action(detail=True, methods=["post"])
    def start_maintenance(self, request, pk):
        instance = self.get_object()

        mode = request.data.get("mode", None)
        duration = request.data.get("duration", None)
        try:
            mode = int(mode)
        except (ValueError, TypeError):
            raise BadRequest(detail={"mode": ["Invalid mode"]})
        if mode not in [MaintainableObject.DEBUG_MAINTENANCE, MaintainableObject.MAINTENANCE]:
            raise BadRequest(detail={"mode": ["Unknown mode"]})
        try:
            duration = int(duration)
        except (ValueError, TypeError):
            raise BadRequest(detail={"duration": ["Invalid duration"]})
        if duration not in MaintainableObject.maintenance_duration_options_in_seconds():
            raise BadRequest(detail={"mode": ["Unknown duration"]})

        try:
            instance.start_maintenance(mode, duration, request.user)
        except MaintenanceCouldNotBeStartedError as e:
            if type(instance) == AlertReceiveChannel:
                detail = {"alert_receive_channel_id": ["Already on maintenance"]}
            else:
                detail = str(e)
            raise BadRequest(detail=detail)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def stop_maintenance(self, request, pk):
        instance = self.get_object()
        user = request.user
        instance.force_disable_maintenance(user)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def migrate(self, request, pk):
        instance = self.get_object()
        integration_type = instance.integration
        if not has_legacy_prefix(integration_type):
            raise BadRequest(detail="Integration is not legacy")

        instance.integration = remove_legacy_prefix(instance.integration)

        # drop all templates since they won't work for new payload shape
        templates = [
            "web_title_template",
            "web_message_template",
            "web_image_url_template",
            "sms_title_template",
            "phone_call_title_template",
            "source_link_template",
            "grouping_id_template",
            "resolve_condition_template",
            "acknowledge_condition_template",
            "slack_title_template",
            "slack_message_template",
            "slack_image_url_template",
            "telegram_title_template",
            "telegram_message_template",
            "telegram_image_url_template",
            "messaging_backends_templates",
        ]

        for f in templates:
            setattr(instance, f, None)

        instance.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def validate_name(self, request):
        """
        Checks if verbal_name is available.
        It is needed for OnCall <-> Alerting integration.
        """
        verbal_name = self.request.query_params.get("verbal_name")
        if verbal_name is None:
            raise BadRequest("verbal_name is required")
        organization = self.request.auth.organization
        name_used = AlertReceiveChannel.objects.filter(organization=organization, verbal_name=verbal_name).exists()
        if name_used:
            r = Response(status=status.HTTP_409_CONFLICT)
        else:
            r = Response(status=status.HTTP_200_OK)

        return r

    @action(detail=True, methods=["get"])
    def connected_contact_points(self, request, pk):
        instance = self.get_object()
        if not instance.is_alerting_integration:
            raise BadRequest(detail="invalid integration")
        contact_points = instance.grafana_alerting_sync_manager.get_connected_contact_points()
        return Response(contact_points)

    @action(detail=False, methods=["get"])
    def contact_points(self, request):
        organization = request.auth.organization
        contact_points = GrafanaAlertingSyncManager.get_contact_points(organization)
        return Response(contact_points)

    @action(detail=True, methods=["post"])
    def connect_contact_point(self, request, pk):
        instance = self.get_object()
        if not instance.is_alerting_integration:
            raise BadRequest(detail="invalid integration")

        datasource_uid = request.data.get("datasource_uid")
        contact_point_name = request.data.get("contact_point_name")
        if not datasource_uid or not contact_point_name:
            raise BadRequest(detail="datasource_uid and contact_point_name are required")
        connected, error = instance.grafana_alerting_sync_manager.connect_contact_point(
            datasource_uid, contact_point_name
        )
        if not connected:
            raise BadRequest(detail=error)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def create_contact_point(self, request, pk):
        instance = self.get_object()
        if not instance.is_alerting_integration:
            raise BadRequest(detail="invalid integration")

        datasource_uid = request.data.get("datasource_uid")
        contact_point_name = request.data.get("contact_point_name")
        if not datasource_uid or not contact_point_name:
            raise BadRequest(detail="datasource_uid and contact_point_name are required")
        created, error = instance.grafana_alerting_sync_manager.connect_contact_point(
            datasource_uid, contact_point_name, create_new=True
        )
        if not created:
            raise BadRequest(detail=error)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def disconnect_contact_point(self, request, pk):
        instance = self.get_object()
        if not instance.is_alerting_integration:
            raise BadRequest(detail="invalid integration")

        datasource_uid = request.data.get("datasource_uid")
        contact_point_name = request.data.get("contact_point_name")
        if not datasource_uid or not contact_point_name:
            raise BadRequest(detail="datasource_uid and contact_point_name are required")
        disconnected, error = instance.grafana_alerting_sync_manager.disconnect_contact_point(
            datasource_uid, contact_point_name
        )
        if not disconnected:
            raise BadRequest(detail=error)
        return Response(status=status.HTTP_200_OK)
