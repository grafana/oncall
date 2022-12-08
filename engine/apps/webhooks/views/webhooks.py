import json
from json import JSONDecodeError

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
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.viewsets import GenericViewSet

from apps.webhooks.models import Webhook
from apps.webhooks.models.webhooks import WebhookLog
from apps.webhooks.serializers.webhooks import WebhookLogSerializer, WebhookSerializer
from apps.webhooks.utils import InvalidWebhookData, InvalidWebhookHeaders, InvalidWebhookTrigger, InvalidWebhookUrl
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
        body = {}
        if len(body_unicode) > 0:
            body = json.loads(body_unicode)

        if len(body) == 0:
            log = WebhookLog.objects.filter(webhook__public_primary_key=pk).first()
            if log:
                body = log.input_data

        if len(body) == 0:
            return HttpResponse(
                json.dumps({"message": "No body in POST to use as event data"}),
                HTTP_400_BAD_REQUEST,
            )

        try:
            trigger_passed, result = instance.check_trigger(body)
            if not trigger_passed:
                return HttpResponse(
                    json.dumps(
                        {
                            "message": "Trigger did not evaluate to true or 1",
                            "trigger_template": instance.trigger_template,
                            "trigger_result": result,
                        }
                    ),
                    status=HTTP_200_OK,
                )
        except InvalidWebhookTrigger as e:
            return HttpResponse(
                json.dumps(
                    {
                        "message": f"Trigger template had errors {e.message}",
                        "trigger_template": instance.trigger_template,
                    }
                ),
                status=HTTP_200_OK,
            )

        try:
            url = instance.build_url(body)
        except InvalidWebhookUrl as e:
            return HttpResponse(
                json.dumps(
                    {
                        "message": f"Invalid URL: {e.message}",
                        "url": instance.url,
                    }
                ),
                status=HTTP_200_OK,
            )

        try:
            request_kwargs = instance.build_request_kwargs(body, raise_data_errors=False)
        except InvalidWebhookHeaders as e:
            return HttpResponse(
                json.dumps(
                    {
                        "message": f"Invalid headers: {e.message}",
                        "headers": instance.headers,
                    }
                ),
                status=HTTP_200_OK,
            )
        except InvalidWebhookData as e:
            return HttpResponse(
                json.dumps(
                    {
                        "message": f"Invalid request data: {e.message}",
                        "data": instance.data,
                    }
                ),
                status=HTTP_200_OK,
            )

        webhook_response = instance.make_request(url, request_kwargs)
        try:
            response_content = webhook_response.json()
        except (JSONDecodeError, TypeError):
            response_content = webhook_response.text
        return HttpResponse(
            json.dumps(
                {
                    "response": {
                        "content": response_content,
                        "status": webhook_response.status_code,
                        "headers": str(webhook_response.headers),
                    }
                }
            ),
            status=HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"status",
    )
    def status(self, request, pk):
        log = WebhookLog.objects.filter(webhook__public_primary_key=pk).first()
        if log:
            return HttpResponse(json.dumps(WebhookLogSerializer(log).data), status=HTTP_200_OK)
        else:
            return HttpResponse(
                json.dumps({"message": "No log found (has webhook been run?)"}), status=HTTP_404_NOT_FOUND
            )
