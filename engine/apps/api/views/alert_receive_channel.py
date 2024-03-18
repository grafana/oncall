import typing

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.plumbing import resolve_type_hint
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel, AlertReceiveChannelConnection
from apps.alerts.models.maintainable_object import MaintainableObject
from apps.api.label_filtering import parse_label_query
from apps.api.permissions import RBACPermission
from apps.api.serializers.alert_receive_channel import (
    AlertReceiveChannelCreateSerializer,
    AlertReceiveChannelSerializer,
    AlertReceiveChannelUpdateSerializer,
    FilterAlertReceiveChannelSerializer,
)
from apps.api.serializers.alert_receive_channel_connection import (
    AlertReceiveChannelConnectedChannelSerializer,
    AlertReceiveChannelConnectionSerializer,
    AlertReceiveChannelNewConnectionSerializer,
)
from apps.api.serializers.webhook import WebhookSerializer
from apps.api.throttlers import DemoAlertThrottler
from apps.api.views.labels import schedule_update_label_cache
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.models.integration_backsync_auth_token import IntegrationBacksyncAuthToken
from apps.integrations.legacy_prefix import has_legacy_prefix, remove_legacy_prefix
from apps.labels.utils import is_labels_feature_enabled
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import NO_TEAM_VALUE, ByTeamModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    FilterSerializerMixin,
    PreviewTemplateException,
    PreviewTemplateMixin,
    PublicPrimaryKeyMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.paginators import FifteenPageSizePaginator
from common.exceptions import (
    BacksyncIntegrationRequestError,
    MaintenanceCouldNotBeStartedError,
    TeamCanNotBeChangedError,
    UnableToSendDemoAlert,
)
from common.insight_log import EntityEvent, write_resource_insight_log


class AlertReceiveChannelCounter(typing.TypedDict):
    alerts_count: int
    alert_groups_count: int


AlertReceiveChannelCounters = dict[str, AlertReceiveChannelCounter]


class AlertReceiveChannelFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    maintenance_mode = filters.MultipleChoiceFilter(
        choices=AlertReceiveChannel.MAINTENANCE_MODE_CHOICES, method="filter_maintenance_mode"
    )
    integration = filters.MultipleChoiceFilter(choices=AlertReceiveChannel.INTEGRATION_CHOICES)
    integration_ne = filters.MultipleChoiceFilter(
        choices=AlertReceiveChannel.INTEGRATION_CHOICES, field_name="integration", exclude=True
    )
    team = TeamModelMultipleChoiceFilter()
    id_ne = filters.ModelMultipleChoiceFilter(
        queryset=lambda request: request.auth.organization.alert_receive_channels.all(),
        field_name="public_primary_key",
        to_field_name="public_primary_key",
        exclude=True,
    )

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


@extend_schema_view(
    list=extend_schema(
        responses=PolymorphicProxySerializer(
            component_name="AlertReceiveChannelPolymorphic",
            serializers=[AlertReceiveChannelSerializer, FilterAlertReceiveChannelSerializer],
            resource_type_field_name=None,
        )
    ),
    update=extend_schema(responses=AlertReceiveChannelUpdateSerializer),
    partial_update=extend_schema(responses=AlertReceiveChannelUpdateSerializer),
)
class AlertReceiveChannelView(
    PreviewTemplateMixin,
    TeamFilteringMixin,
    PublicPrimaryKeyMixin[AlertReceiveChannel],
    FilterSerializerMixin,
    CreateSerializerMixin,
    UpdateSerializerMixin,
    ModelViewSet,
):
    """
    Internal API endpoints for alert receive channels (integrations).
    """

    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)

    model = AlertReceiveChannel
    queryset = AlertReceiveChannel.objects.none()  # needed for drf-spectacular introspection
    serializer_class = AlertReceiveChannelSerializer
    filter_serializer_class = FilterAlertReceiveChannelSerializer
    create_serializer_class = AlertReceiveChannelCreateSerializer
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
        "test_connection": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "status_options": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "webhooks_get": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "webhooks_post": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "webhooks_put": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "webhooks_delete": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "connected_alert_receive_channels_get": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "connected_alert_receive_channels_post": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "connected_alert_receive_channels_put": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "connected_alert_receive_channels_delete": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "backsync_token_get": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "backsync_token_post": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
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

    def destroy(self, request, *args, **kwargs):
        # don't allow deleting direct paging integrations
        instance = self.get_object()
        if instance.integration == AlertReceiveChannel.INTEGRATION_DIRECT_PAGING:
            raise BadRequest(detail="Direct paging integrations can't be deleted")

        return super().destroy(request, *args, **kwargs)

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

        # filter labels
        label_query = self.request.query_params.getlist("label", [])
        kv_pairs = parse_label_query(label_query)
        for key, value in kv_pairs:
            queryset = queryset.filter(
                labels__key_id=key,
                labels__value_id=value,
            )

        # distinct to remove duplicates after alert_receive_channels X labels join
        queryset = queryset.distinct()

        return queryset

    def paginate_queryset(self, queryset):
        """
        If `skip_pagination` is provided and is equal to "true" (or "True"), it will return
        a non paginated list of results. This is useful for Grafana Alerting
        """
        if self.request.query_params.get("skip_pagination", "false").lower() == "true":
            return None
        page = super().paginate_queryset(queryset)
        if page is not None:
            ids = [d.id for d in queryset]
            schedule_update_label_cache(self.model.__name__, self.request.auth.organization, ids)
        return page

    @extend_schema(
        request=inline_serializer(
            name="AlertReceiveChannelSendDemoAlert",
            fields={
                "demo_alert_payload": serializers.DictField(required=False, allow_null=True),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
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

    def _backsync_integration_request(self, instance, func_name):
        integration_func = getattr(instance.config, func_name, None)
        if integration_func:
            try:
                return integration_func(instance)
            except BacksyncIntegrationRequestError as e:
                raise BadRequest(detail=e.error_msg)

    @extend_schema(
        request=AlertReceiveChannelSerializer,
        responses={status.HTTP_200_OK: None},
    )
    @action(detail=False, methods=["post"])
    def test_connection(self, request):
        # create in-memory instance to test with the (possible) unsaved data
        data = request.data
        # clear name while testing connection (to avoid name already used validation error)
        data["verbal_name"] = None
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = AlertReceiveChannel(**serializer.validated_data)

        # will raise if there are errors
        self._backsync_integration_request(instance, "test_connection")

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        responses=inline_serializer(
            name="AlertReceiveChannelBacksyncStatusOptions",
            fields={
                "value": serializers.CharField(),
                "display_name": serializers.CharField(),
            },
            many=True,
        ),
    )
    @action(detail=True, methods=["get"])
    def status_options(self, request, pk):
        instance = self.get_object()
        choices = self._backsync_integration_request(instance, "status_options")
        if choices is None:
            choices = []
        return Response(choices)

    @extend_schema(
        responses=inline_serializer(
            name="AlertReceiveChannelIntegrationOptions",
            fields={
                "value": serializers.CharField(),
                "display_name": serializers.CharField(),
                "short_description": serializers.CharField(),
                "featured": serializers.BooleanField(),
                "featured_tag_name": serializers.CharField(allow_null=True),
            },
            many=True,
        )
    )
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

    @extend_schema(
        parameters=[
            inline_serializer(name="AlertReceiveChannelChangeTeam", fields={"team_id": serializers.CharField()})
        ],
        request=None,
        responses={status.HTTP_200_OK: None},
    )
    @action(detail=True, methods=["put"])
    def change_team(self, request, pk):
        instance = self.get_object()

        if "team_id" not in request.query_params:
            raise BadRequest(detail="team_id must be specified")

        team_id = request.query_params["team_id"]
        if team_id == NO_TEAM_VALUE:
            team_id = None

        try:
            instance.change_team(team_id=team_id, user=self.request.user)
        except TeamCanNotBeChangedError as e:
            raise BadRequest(detail=e)

        return Response()

    @extend_schema(responses={status.HTTP_200_OK: resolve_type_hint(AlertReceiveChannelCounters)})
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

    @extend_schema(
        # make operation_id unique, otherwise drf-spectacular will issue a warning
        operation_id="alert_receive_channels_counters_per_integration_retrieve",
        responses={status.HTTP_200_OK: resolve_type_hint(AlertReceiveChannelCounters)},
    )
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

    @extend_schema(
        responses=inline_serializer(
            name="AlertReceiveChannelFilters",
            fields={
                "name": serializers.CharField(),
                "display_name": serializers.CharField(required=False),
                "type": serializers.CharField(),
                "href": serializers.CharField(),
                "global": serializers.BooleanField(required=False),
            },
            many=True,
        )
    )
    @action(methods=["get"], detail=False)
    def filters(self, request):
        organization = self.request.auth.organization
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

        if is_labels_feature_enabled(organization):
            filter_options.append(
                {
                    "name": "label",
                    "display_name": "Label",
                    "type": "labels",
                }
            )

        return Response(filter_options)

    @extend_schema(
        request=inline_serializer(
            name="AlertReceiveChannelStartMaintenance",
            fields={
                "mode": serializers.ChoiceField(choices=MaintainableObject.MAINTENANCE_MODE_CHOICES),
                "duration": serializers.ChoiceField(
                    choices=MaintainableObject.maintenance_duration_options_in_seconds()
                ),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
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

    @extend_schema(request=None, responses={status.HTTP_200_OK: None})
    @action(detail=True, methods=["post"])
    def stop_maintenance(self, request, pk):
        instance = self.get_object()
        instance.force_disable_maintenance(request.user)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(request=None, responses={status.HTTP_200_OK: None})
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

    @extend_schema(
        parameters=[
            inline_serializer(
                name="AlertReceiveChannelValidateName",
                fields={
                    "verbal_name": serializers.CharField(),
                },
            )
        ],
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_409_CONFLICT: None,
        },
    )
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

    @extend_schema(
        responses=inline_serializer(
            name="AlertReceiveChannelConnectedContactPoints",
            fields={
                "uid": serializers.CharField(),
                "name": serializers.CharField(),
                "contact_points": inline_serializer(
                    "AlertReceiveChannelConnectedContactPointsInner",
                    fields={"name": serializers.CharField(), "notification_connected": serializers.BooleanField()},
                    many=True,
                ),
            },
            many=True,
        )
    )
    @action(detail=True, methods=["get"])
    def connected_contact_points(self, request, pk):
        instance = self.get_object()
        if not instance.is_alerting_integration:
            raise BadRequest(detail="invalid integration")
        contact_points = instance.grafana_alerting_sync_manager.get_connected_contact_points()
        return Response(contact_points)

    @extend_schema(
        responses=inline_serializer(
            name="AlertReceiveChannelContactPoints",
            fields={
                "uid": serializers.CharField(),
                "name": serializers.CharField(),
                "contact_points": serializers.ListField(child=serializers.CharField()),
            },
            many=True,
        )
    )
    @action(detail=False, methods=["get"])
    def contact_points(self, request):
        organization = request.auth.organization
        contact_points = GrafanaAlertingSyncManager.get_contact_points(organization)
        return Response(contact_points)

    @extend_schema(
        request=inline_serializer(
            name="AlertReceiveChannelConnectContactPoint",
            fields={
                "datasource_uid": serializers.CharField(),
                "contact_point_name": serializers.CharField(),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
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

    @extend_schema(
        request=inline_serializer(
            name="AlertReceiveChannelCreateContactPoint",
            fields={
                "datasource_uid": serializers.CharField(),
                "contact_point_name": serializers.CharField(),
            },
        ),
        responses={status.HTTP_201_CREATED: None},
    )
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

    @extend_schema(
        request=inline_serializer(
            name="AlertReceiveChannelDisconnectContactPoint",
            fields={
                "datasource_uid": serializers.CharField(),
                "contact_point_name": serializers.CharField(),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
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

    @extend_schema(request=None, responses=WebhookSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="webhooks")
    def webhooks_get(self, request, pk):
        instance = self.get_object()
        return Response(
            WebhookSerializer(
                instance.webhooks.filter(is_from_connected_integration=True),
                many=True,
                context={"request": request},
            ).data
        )

    @extend_schema(request=WebhookSerializer, responses=WebhookSerializer)
    @webhooks_get.mapping.post
    # https://www.django-rest-framework.org/api-guide/viewsets/#routing-additional-http-methods-for-extra-actions
    def webhooks_post(self, request, pk):
        instance = self.get_object()
        serializer = WebhookSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(filtered_integrations=[instance], is_from_connected_integration=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=WebhookSerializer, responses=WebhookSerializer)
    @action(detail=True, methods=["put"], url_path=r"webhooks/(?P<webhook_id>\w+)")
    def webhooks_put(self, request, pk, webhook_id):
        instance = self.get_object()
        try:
            webhook = instance.webhooks.get(is_from_connected_integration=True, public_primary_key=webhook_id)
        except ObjectDoesNotExist:
            raise NotFound
        serializer = WebhookSerializer(webhook, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None, responses=None)
    @webhooks_put.mapping.delete
    # https://www.django-rest-framework.org/api-guide/viewsets/#routing-additional-http-methods-for-extra-actions
    def webhooks_delete(self, request, pk, webhook_id):
        instance = self.get_object()
        try:
            webhook = instance.webhooks.get(is_from_connected_integration=True, public_primary_key=webhook_id)
        except ObjectDoesNotExist:
            raise NotFound
        webhook.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None, responses=AlertReceiveChannelConnectionSerializer)
    @action(detail=True, methods=["get"], url_path="connected_alert_receive_channels")
    def connected_alert_receive_channels_get(self, request, pk):
        instance = self.get_object()
        return Response(AlertReceiveChannelConnectionSerializer(instance).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AlertReceiveChannelNewConnectionSerializer(many=True), responses=AlertReceiveChannelConnectionSerializer
    )
    @connected_alert_receive_channels_get.mapping.post
    def connected_alert_receive_channels_post(self, request, pk):
        instance = self.get_object()
        serializer = AlertReceiveChannelNewConnectionSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        backsync_map = {connection["id"]: connection["backsync"] for connection in serializer.validated_data}

        # bulk create connections
        AlertReceiveChannelConnection.objects.bulk_create(
            [
                AlertReceiveChannelConnection(
                    source_alert_receive_channel=instance,
                    connected_alert_receive_channel=alert_receive_channel,
                    backsync=backsync_map[alert_receive_channel.public_primary_key],
                )
                for alert_receive_channel in instance.organization.alert_receive_channels.filter(
                    public_primary_key__in=backsync_map.keys()
                )
            ],
            ignore_conflicts=True,
            batch_size=5000,
        )

        return Response(AlertReceiveChannelConnectionSerializer(instance).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=AlertReceiveChannelConnectedChannelSerializer,
        responses=AlertReceiveChannelConnectedChannelSerializer,
    )
    @action(
        detail=True,
        methods=["put"],
        url_path=r"connected_alert_receive_channels/(?P<connected_alert_receive_channel_id>\w+)",
    )
    def connected_alert_receive_channels_put(self, request, pk, connected_alert_receive_channel_id):
        instance = self.get_object()
        try:
            connection = instance.connected_alert_receive_channels.get(
                connected_alert_receive_channel_id__public_primary_key=connected_alert_receive_channel_id
            )
        except ObjectDoesNotExist:
            raise NotFound

        serializer = AlertReceiveChannelConnectedChannelSerializer(connection, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None, responses=None)
    @connected_alert_receive_channels_put.mapping.delete
    def connected_alert_receive_channels_delete(self, request, pk, connected_alert_receive_channel_id):
        instance = self.get_object()
        try:
            connection = instance.connected_alert_receive_channels.get(
                connected_alert_receive_channel_id__public_primary_key=connected_alert_receive_channel_id
            )
        except ObjectDoesNotExist:
            raise NotFound

        connection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses={status.HTTP_200_OK: None})
    @action(detail=True, methods=["get"], url_path="api_token")
    def backsync_token_get(self, request, pk):
        instance = self.get_object()
        try:
            _ = IntegrationBacksyncAuthToken.objects.get(
                alert_receive_channel=instance, organization=request.auth.organization
            )
        except IntegrationBacksyncAuthToken.DoesNotExist:
            raise NotFound

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        methods=["post"],
        request=None,
        responses=inline_serializer(
            name="IntegrationTokenPostResponse",
            fields={
                "token": serializers.CharField(),
            },
        ),
    )
    @action(detail=True, methods=["post"], url_path="api_token")
    @backsync_token_get.mapping.post
    def backsync_token_post(self, request, pk):
        instance = self.get_object()
        instance, token = IntegrationBacksyncAuthToken.create_auth_token(instance, request.auth.organization)
        data = {"token": token}
        return Response(data, status=status.HTTP_201_CREATED)
