from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import ChannelFilter
from apps.api.permissions import RBACPermission
from apps.api.serializers.channel_filter import (
    ChannelFilterCreateSerializer,
    ChannelFilterSerializer,
    ChannelFilterUpdateResponseSerializer,
    ChannelFilterUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ModelFieldFilterMixin, MultipleChoiceCharFilter, get_integration_queryset
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.insight_log import EntityEvent, write_resource_insight_log
from common.ordered_model.viewset import OrderedModelViewSet


class ChannelFilterFilter(ModelFieldFilterMixin, filters.FilterSet):
    alert_receive_channel = MultipleChoiceCharFilter(
        queryset=get_integration_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )


@extend_schema_view(
    list=extend_schema(responses=ChannelFilterSerializer),
    create=extend_schema(request=ChannelFilterCreateSerializer, responses=ChannelFilterUpdateResponseSerializer),
    update=extend_schema(request=ChannelFilterUpdateSerializer, responses=ChannelFilterUpdateResponseSerializer),
    partial_update=extend_schema(
        request=ChannelFilterUpdateSerializer, responses=ChannelFilterUpdateResponseSerializer
    ),
)
class ChannelFilterView(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin[ChannelFilter],
    CreateSerializerMixin,
    UpdateSerializerMixin,
    OrderedModelViewSet,
):
    """
    Internal API endpoints for channel filters (routes).
    """

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "list": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "retrieve": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "create": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "partial_update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "destroy": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "move_to_position": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "convert_from_regex_to_jinja2": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
    }

    queryset = ChannelFilter.objects.none()  # needed for drf-spectacular introspection

    model = ChannelFilter
    serializer_class = ChannelFilterSerializer
    update_serializer_class = ChannelFilterUpdateSerializer
    create_serializer_class = ChannelFilterCreateSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ChannelFilterFilter

    TEAM_LOOKUP = "alert_receive_channel__team"

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        queryset = ChannelFilter.objects.filter(
            alert_receive_channel__organization=self.request.auth.organization,
            alert_receive_channel__deleted_at=None,
        )

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        return self.serializer_class.setup_eager_loading(queryset)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default:
            raise BadRequest(detail="Unable to delete default filter")
        else:
            write_resource_insight_log(
                instance=instance,
                author=self.request.user,
                event=EntityEvent.DELETED,
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

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

    @extend_schema(request=None, responses={status.HTTP_200_OK: None})
    @action(detail=True, methods=["put"])
    def move_to_position(self, request, pk):
        instance = self.get_object()
        if instance.is_default:
            raise BadRequest(detail="Unable to change position for default filter")

        return super().move_to_position(request, pk)

    @extend_schema(request=None, responses=ChannelFilterSerializer)
    @action(detail=True, methods=["post"])
    def convert_from_regex_to_jinja2(self, request, pk):
        instance = self.get_object()
        if not instance.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX:
            raise BadRequest(detail="Only regex filtering term type is supported")

        serializer_class = self.serializer_class

        instance.filtering_term = serializer_class(instance).get_filtering_term_as_jinja2(instance)
        instance.filtering_term_type = ChannelFilter.FILTERING_TERM_TYPE_JINJA2
        instance.save()
        return Response(status=status.HTTP_200_OK, data=serializer_class(instance).data)
