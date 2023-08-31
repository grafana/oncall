from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.webhooks import (
    WebhookCreateSerializer,
    WebhookResponseSerializer,
    WebhookUpdateSerializer,
)
from apps.public_api.throttlers import UserThrottle
from apps.webhooks.models import Webhook, WebhookResponse
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log


class WebhooksView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    model = Webhook
    serializer_class = WebhookCreateSerializer
    update_serializer_class = WebhookUpdateSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        webhook_name = self.request.query_params.get("name", None)
        queryset = Webhook.objects.filter(organization=self.request.auth.organization)

        if webhook_name:
            queryset = queryset.filter(name=webhook_name)

        return queryset.order_by("id")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return Webhook.objects.filter(organization=self.request.auth.organization).get(
                public_primary_key=public_primary_key
            )
        except Webhook.DoesNotExist:
            raise NotFound

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

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    @action(methods=["get"], detail=True)
    def responses(self, request, pk):
        webhook = self.get_object()
        queryset = WebhookResponse.objects.filter(webhook_id=webhook.id, trigger_type=webhook.trigger_type).order_by(
            "-timestamp"
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            response_serializer = WebhookResponseSerializer(page, many=True)
            return self.get_paginated_response(response_serializer.data)

        response_serializer = WebhookResponseSerializer(queryset, many=True)
        return Response(response_serializer.data)
