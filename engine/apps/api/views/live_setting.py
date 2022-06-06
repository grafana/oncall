from contextlib import suppress

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from telegram import error

from apps.api.permissions import IsAdmin
from apps.api.serializers.live_setting import LiveSettingSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.oss_installation.models import CloudConnector
from apps.slack.tasks import unpopulate_slack_user_identities
from apps.telegram.client import TelegramClient
from apps.telegram.tasks import register_telegram_webhook
from apps.user_management.models import User
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class LiveSettingViewSet(PublicPrimaryKeyMixin, viewsets.ModelViewSet):
    serializer_class = LiveSettingSerializer
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def dispatch(self, request, *args, **kwargs):
        if not settings.FEATURE_LIVE_SETTINGS_ENABLED:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        LiveSetting.populate_settings_if_needed()
        return LiveSetting.objects.filter(name__in=LiveSetting.AVAILABLE_NAMES).order_by("name")

    def perform_update(self, serializer):
        new_value = serializer.validated_data["value"]
        self._update_hook(new_value)

        super().perform_update(serializer)

    def perform_destroy(self, instance):
        new_value = instance.default_value
        self._update_hook(new_value)

        super().perform_destroy(instance)

    def _update_hook(self, new_value):
        instance = self.get_object()

        if instance.name == "TELEGRAM_TOKEN":
            try:
                old_token = live_settings.TELEGRAM_TOKEN
            except ImproperlyConfigured:
                old_token = None

            if old_token != new_value:
                self._reset_telegram_integration(new_token=new_value)

        for setting_name in ["SLACK_CLIENT_OAUTH_ID", "SLACK_CLIENT_OAUTH_SECRET"]:
            if instance.name == setting_name:
                if getattr(live_settings, setting_name) != new_value:
                    organization = self.request.auth.organization
                    sti = organization.slack_team_identity
                    if sti is not None:
                        unpopulate_slack_user_identities.apply_async((sti.pk, True), countdown=0)

        if instance.name == "GRAFANA_CLOUD_ONCALL_TOKEN":
            try:
                old_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
            except ImproperlyConfigured:
                old_token = None

            if old_token != new_value:
                CloudConnector.remove_sync()

    def _reset_telegram_integration(self, new_token):
        # tell Telegram to cancel sending events from old bot
        with suppress(ImproperlyConfigured, error.InvalidToken, error.Unauthorized):
            old_client = TelegramClient()
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

        # tell Telegram to send updates to new bot
        register_telegram_webhook.delay(token=new_token)
