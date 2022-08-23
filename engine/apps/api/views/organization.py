from contextlib import suppress

from django.apps import apps
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import AnyRole, IsAdmin, MethodPermission
from apps.api.serializers.organization import CurrentOrganizationSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.base.messaging import get_messaging_backend_from_id
from apps.telegram.client import TelegramClient
from common.insight_log import EntityEvent, write_resource_insight_log


class CurrentOrganizationView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, MethodPermission)

    method_permissions = {IsAdmin: ("PUT",), AnyRole: ("GET",)}

    def get(self, request):
        organization = request.auth.organization
        serializer = CurrentOrganizationSerializer(organization, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        organization = self.request.auth.organization
        prev_state = organization.insight_logs_serialized
        serializer = CurrentOrganizationSerializer(
            instance=organization, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )
        return Response(serializer.data)


class GetTelegramVerificationCode(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        organization = request.auth.organization
        user = request.user
        TelegramChannelVerificationCode = apps.get_model("telegram", "TelegramChannelVerificationCode")
        with suppress(TelegramChannelVerificationCode.DoesNotExist):
            existing_verification_code = organization.telegram_verification_code
            existing_verification_code.delete()
        new_code = TelegramChannelVerificationCode.objects.create(organization=organization, author=user)
        telegram_client = TelegramClient()
        bot_username = telegram_client.api_client.username
        bot_link = f"https://t.me/{bot_username}"
        return Response({"telegram_code": str(new_code.uuid), "bot_link": bot_link}, status=status.HTTP_200_OK)


class GetChannelVerificationCode(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        organization = request.auth.organization
        backend_id = request.query_params.get("backend")
        backend = get_messaging_backend_from_id(backend_id)
        if backend is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        code = backend.generate_channel_verification_code(organization)
        return Response(code)


class SetGeneralChannel(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def post(self, request):
        SlackChannel = apps.get_model("slack", "SlackChannel")
        organization = request.auth.organization
        slack_team_identity = organization.slack_team_identity
        slack_channel_id = request.data["id"]

        slack_channel = SlackChannel.objects.get(
            public_primary_key=slack_channel_id, slack_team_identity=slack_team_identity
        )

        organization.set_general_log_channel(slack_channel.slack_id, slack_channel.name, request.user)

        return Response(status=200)
