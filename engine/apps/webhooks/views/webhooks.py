import json

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from apps.webhooks.models import Webhook
from apps.webhooks.serializers.webhooks import WebhookSerializer
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class WebhooksView(
    PublicPrimaryKeyMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    permission_classes = [AllowAny]

    model = Webhook
    serializer_class = WebhookSerializer

    def get_queryset(self):
        return Webhook.objects.all()

    @action(
        detail=True,
        methods=["post"],
        url_path=r"test",
    )
    def test_webhook(self, request, pk):
        instance = self.get_object()
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        webhook_response = instance.make_request(body)
        return HttpResponse(
            content=webhook_response.content,
            status=webhook_response.status_code,
            content_type=webhook_response.headers["Content-Type"],
        )
