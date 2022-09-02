from django.db.models import Count
from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.tasks import update_verbose_name_for_alert_receive_channel
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import IntegrationSerializer, IntegrationUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import FilterSerializerMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log

from .maintaiable_object_mixin import MaintainableObjectMixin


class IntegrationView(
    RateLimitHeadersMixin,
    FilterSerializerMixin,
    UpdateSerializerMixin,
    MaintainableObjectMixin,
    ModelViewSet,
):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = AlertReceiveChannel
    serializer_class = IntegrationSerializer
    update_serializer_class = IntegrationUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        queryset = AlertReceiveChannel.objects.filter(organization=self.request.auth.organization).order_by(
            "created_at"
        )
        name = self.request.query_params.get("name", None)
        if name is not None:
            queryset = queryset.filter(verbal_name=name)
        queryset = self.filter_queryset(queryset)
        queryset = self.serializer_class.setup_eager_loading(queryset)
        queryset = queryset.annotate(alert_groups_count_annotated=Count("alert_groups", distinct=True))
        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return self.get_queryset().get(public_primary_key=public_primary_key)
        except AlertReceiveChannel.DoesNotExist:
            raise NotFound

    def perform_update(self, serializer):
        instance = serializer.instance

        prev_state = instance.insight_logs_serialized
        prev_web_title_template = instance.web_title_template

        serializer.save()

        new_state = instance.insight_logs_serialized
        new_web_title_template = instance.web_title_template

        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

        if new_web_title_template != prev_web_title_template:
            update_verbose_name_for_alert_receive_channel.delay(instance.pk)

    def perform_destroy(self, instance):
        write_resource_insight_log(instance=instance, author=self.request.user, event=EntityEvent.DELETED)
        instance.delete()
