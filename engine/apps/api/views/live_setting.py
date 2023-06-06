from contextlib import suppress

from django.conf import settings
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from telegram import error

from apps.api.permissions import RBACPermission
from apps.api.serializers.live_setting import LiveSettingSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.base.models import LiveSetting
from apps.oss_installation.tasks import sync_users_with_cloud
from apps.slack.tasks import unpopulate_slack_user_identities
from apps.telegram.client import TelegramClient
from apps.telegram.tasks import register_telegram_webhook
from apps.user_management.models import User
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class LiveSettingViewSet(PublicPrimaryKeyMixin, viewsets.ModelViewSet):
    serializer_class = LiveSettingSerializer
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "list": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
        "retrieve": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
        "create": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
        "update": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
        "destroy": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    def dispatch(self, request, *args, **kwargs):
        if not settings.FEATURE_LIVE_SETTINGS_ENABLED:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        LiveSetting.populate_settings_if_needed()
        queryset = LiveSetting.objects.filter(name__in=LiveSetting.AVAILABLE_NAMES).order_by("name")
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(name=search)
        return queryset

    def perform_update(self, serializer):
        name = serializer.instance.name
        old_value = serializer.instance.value
        new_value = serializer.validated_data["value"]

        super().perform_update(serializer)

        if new_value != old_value:
            self._post_update_hook(name, old_value)
            LiveSetting.validate_settings()

    def perform_destroy(self, instance):
        name = instance.name
        old_value = instance.value
        new_value = instance.default_value

        super().perform_destroy(instance)

        if new_value != old_value:
            self._post_update_hook(name, old_value)

    def _post_update_hook(self, name, old_value):
        if name == "TELEGRAM_TOKEN":
            self._reset_telegram_integration(old_token=old_value)
            register_telegram_webhook.delay()

        if name in ["SLACK_CLIENT_OAUTH_ID", "SLACK_CLIENT_OAUTH_SECRET"]:
            organization = self.request.auth.organization
            slack_team_identity = organization.slack_team_identity
            if slack_team_identity is not None:
                unpopulate_slack_user_identities.delay(organization_pk=organization.pk, force=True)

        if name == "GRAFANA_CLOUD_ONCALL_TOKEN":
            from apps.oss_installation.models import CloudConnector

            CloudConnector.remove_sync()

            sync_users = self.request.query_params.get("sync_users", "true") == "true"
            if sync_users:
                sync_users_with_cloud.apply_async()

    def _reset_telegram_integration(self, old_token):
        # tell Telegram to cancel sending events from old bot
        with suppress(error.InvalidToken, error.Unauthorized):
            old_client = TelegramClient(token=old_token)
            old_client.api_client.delete_webhook()

        # delete telegram channels for current team
        organization = self.request.auth.organization
        organization.telegram_channel.all().delete()

        # delete telegram connectors for users in team
        users_with_telegram_connector = User.objects.filter(
            organization=organization, telegram_connection__isnull=False
        ).distinct()

        for user in users_with_telegram_connector:
            user.telegram_connection.delete()
