from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import ResolutionNote
from apps.alerts.tasks import send_update_resolution_note_signal
from apps.api.permissions import RBACPermission
from apps.auth_token.auth import ApiTokenAuthentication, GrafanaServiceAccountAuthentication
from apps.public_api.serializers.resolution_notes import ResolutionNoteSerializer, ResolutionNoteUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class ResolutionNoteView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (GrafanaServiceAccountAuthentication, ApiTokenAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "list": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "retrieve": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "create": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "update": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "partial_update": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "destroy": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    throttle_classes = [UserThrottle]

    model = ResolutionNote
    serializer_class = ResolutionNoteSerializer
    update_serializer_class = ResolutionNoteUpdateSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["alert_group"]

    pagination_class = FiftyPageSizePaginator

    def get_queryset(self):
        alert_group_id = self.request.query_params.get("alert_group_id", None)
        queryset = ResolutionNote.objects.filter(
            alert_group__channel__organization=self.request.auth.organization,
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        if alert_group_id:
            queryset = queryset.filter(alert_group__public_primary_key=alert_group_id)
        return queryset.order_by("-alert_group__started_at")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]
        queryset = self.filter_queryset(self.get_queryset())
        try:
            return queryset.get(public_primary_key=public_primary_key)
        except ResolutionNote.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        super().perform_create(serializer)
        send_update_resolution_note_signal.apply_async((serializer.instance.alert_group.pk, serializer.instance.pk))

    def perform_update(self, serializer):
        is_text_updated = serializer.instance.message_text != serializer.validated_data["message_text"]
        super().perform_update(serializer)
        if is_text_updated:
            send_update_resolution_note_signal.apply_async((serializer.instance.alert_group.pk, serializer.instance.pk))

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        send_update_resolution_note_signal.apply_async((instance.alert_group.pk, instance.pk))
