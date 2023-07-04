from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import ResolutionNote
from apps.alerts.tasks import send_update_resolution_note_signal
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.resolution_notes import ResolutionNoteSerializer, ResolutionNoteUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class ResolutionNoteView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

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

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)

        # send signal to update alert group and resolution_note
        method = request.method.lower()
        if method in ["post", "put", "patch", "delete"]:
            instance_id = self.kwargs.get("pk") or result.data.get("id")
            if instance_id:
                instance = ResolutionNote.objects_with_deleted.filter(public_primary_key=instance_id).first()
                if instance is not None:
                    send_update_resolution_note_signal.apply_async(
                        kwargs={
                            "alert_group_pk": instance.alert_group.pk,
                            "resolution_note_pk": instance.pk,
                        }
                    )
        return result
