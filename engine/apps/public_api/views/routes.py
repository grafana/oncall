from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import ChannelFilter
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers import ChannelFilterSerializer, ChannelFilterUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import DemoTokenMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import TwentyFivePageSizePaginator


class ChannelFilterView(RateLimitHeadersMixin, DemoTokenMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = ChannelFilter
    serializer_class = ChannelFilterSerializer
    update_serializer_class = ChannelFilterUpdateSerializer

    pagination_class = TwentyFivePageSizePaginator

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["alert_receive_channel"]

    demo_default_id = public_api_constants.DEMO_ROUTE_ID_1

    def get_queryset(self):
        integration_id = self.request.query_params.get("integration_id", None)
        routing_regex = self.request.query_params.get("routing_regex", None)

        queryset = ChannelFilter.objects.filter(
            alert_receive_channel__organization=self.request.auth.organization, alert_receive_channel__deleted_at=None
        )

        if integration_id:
            queryset = queryset.filter(alert_receive_channel__public_primary_key=integration_id)
        if routing_regex:
            queryset = queryset.filter(filtering_term=routing_regex)
        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return ChannelFilter.objects.filter(
                alert_receive_channel__organization=self.request.auth.organization,
                alert_receive_channel__deleted_at=None,
            ).get(public_primary_key=public_primary_key)
        except ChannelFilter.DoesNotExist:
            raise NotFound

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default:
            raise BadRequest(detail="Unable to delete default filter")
        else:
            alert_receive_channel = instance.alert_receive_channel
            user = self.request.user
            route_verbal = instance.verbal_name_for_clients.capitalize()
            description = f"{route_verbal} of integration {alert_receive_channel.verbal_name} was deleted"
            create_organization_log(
                alert_receive_channel.organization,
                user,
                OrganizationLogType.TYPE_CHANNEL_FILTER_DELETED,
                description,
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        alert_receive_channel = instance.alert_receive_channel
        user = self.request.user
        route_verbal = instance.verbal_name_for_clients.capitalize()
        description = f"{route_verbal} was created for integration {alert_receive_channel.verbal_name}"
        create_organization_log(
            alert_receive_channel.organization,
            user,
            OrganizationLogType.TYPE_CHANNEL_FILTER_CREATED,
            description,
        )

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        alert_receive_channel = serializer.instance.alert_receive_channel
        route_verbal = serializer.instance.verbal_name_for_clients.capitalize()
        description = (
            f"Settings for {route_verbal} of integration {alert_receive_channel.verbal_name} "
            f"was changed from:\n{old_state}\nto:\n{new_state}"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_CHANGED, description)
