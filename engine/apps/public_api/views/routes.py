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
from common.insight_log import EntityEvent, write_resource_insight_log


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
