import hashlib
import hmac
import logging

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.zoom.auth import ZoomEventAuthentication, ZoomWebhookAuthentication
from apps.zoom.events.event_manager import EventManager
from apps.zoom.models import ZoomChannel
from apps.zoom.serializers import ZoomChannelSerializer
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log

logger = logging.getLogger(__name__)


class ZoomChannelViewSet(
    PublicPrimaryKeyMixin[ZoomChannel],
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing Zoom channels."""
    
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "list": [RBACPermission.Permissions.CHATOPS_READ],
        "retrieve": [RBACPermission.Permissions.CHATOPS_READ],
        "create": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "destroy": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "set_default": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    serializer_class = ZoomChannelSerializer

    def get_queryset(self):
        return ZoomChannel.objects.filter(organization=self.request.user.organization)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk):
        """Set a channel as the default channel for the organization."""
        zoom_channel = self.get_object()
        zoom_channel.make_channel_default(request.user)
        return Response(status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_CONNECTED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=instance.channel_name,
        )

    def perform_destroy(self, instance):
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=instance.channel_name,
            channel_id=instance.channel_id,
        )
        instance.delete()


class ZoomEventView(APIView):
    """View for handling Zoom interactive message events (button clicks)."""
    
    authentication_classes = (ZoomEventAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    def get(self, request, format=None):
        return Response("hello")

    def post(self, request):
        """Handle interactive message action from Zoom."""
        EventManager.process_interactive_action(request=request)
        return Response(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class ZoomWebhookView(APIView):
    """
    View for handling Zoom webhooks.
    
    This handles:
    - URL validation challenge
    - Bot notifications
    - Interactive message actions
    """
    
    authentication_classes = []  # No authentication for webhooks
    permission_classes = []  # No permission required for webhooks

    def post(self, request):
        """Handle incoming Zoom webhook events."""
        event_type = request.data.get("event", "")
        
        # Handle URL validation challenge
        if event_type == "endpoint.url_validation":
            return self._handle_url_validation(request)
        
        # Process other events
        logger.info(f"Received Zoom webhook event: {event_type}")
        EventManager.process_webhook(request=request)
        
        return Response(status=200)

    def _handle_url_validation(self, request):
        """
        Handle Zoom URL validation challenge.
        
        Reference: https://developers.zoom.us/docs/api/rest/webhook-reference/#validate-your-webhook-endpoint
        """
        payload = request.data.get("payload", {})
        plain_token = payload.get("plainToken", "")
        
        if not plain_token:
            return Response({"error": "Missing plainToken"}, status=400)
        
        secret_token = getattr(settings, "ZOOM_WEBHOOK_SECRET_TOKEN", "")
        if not secret_token:
            logger.error("ZOOM_WEBHOOK_SECRET_TOKEN is not configured")
            return Response({"error": "Server configuration error"}, status=500)
        
        # Generate the hash
        hash_value = hmac.new(
            secret_token.encode("utf-8"),
            plain_token.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return Response({
            "plainToken": plain_token,
            "encryptedToken": hash_value,
        })
