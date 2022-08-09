from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import ChannelFilter
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import ChannelFilterSerializer, ChannelFilterUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import TwentyFivePageSizePaginator
from common.insight_logs import entity_created_insight_logs, entity_deleted_insight_logs, entity_updated_insight_logs


class ChannelFilterView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = ChannelFilter
    serializer_class = ChannelFilterSerializer
    update_serializer_class = ChannelFilterUpdateSerializer

    pagination_class = TwentyFivePageSizePaginator

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["alert_receive_channel"]

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
            user = self.request.user
            entity_deleted_insight_logs(
                user,
                instance,
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        user = self.request.user
        entity_created_insight_logs(instance=instance, user=user)

    def perform_update(self, serializer):
        user = self.request.user
        old_state = serializer.instance.insight_logs_dict
        serializer.save()
        new_state = serializer.instance.insight_logs_dict
        entity_updated_insight_logs(user, serializer.instance, old_state, new_state)
