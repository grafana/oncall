from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, IsAdmin
from apps.api.serializers.public_api_token import PublicApiTokenSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import MAX_PUBLIC_API_TOKENS_PER_USER
from apps.auth_token.models import ApiAuthToken
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest


class PublicApiTokenView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [PluginAuthentication]
    permission_classes = [IsAuthenticated]

    action_permissions = {IsAdmin: (*MODIFY_ACTIONS, *READ_ACTIONS)}

    model = ApiAuthToken
    serializer_class = PublicApiTokenSerializer

    def get_queryset(self):
        return ApiAuthToken.objects.filter(user=self.request.user, organization=self.request.user.organization)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        description = f"API token {instance.name} was revoked"
        create_organization_log(user.organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_DELETED, description)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        user = request.user
        token_name = request.data.get("name")

        if (
            ApiAuthToken.objects.filter(user=user, organization=user.organization).count()
            >= MAX_PUBLIC_API_TOKENS_PER_USER
        ):
            raise BadRequest("Max token count")

        if token_name is None or token_name == "":
            raise BadRequest("Invalid token name")
        instance, token = ApiAuthToken.create_auth_token(user, user.organization, token_name)
        data = {"id": instance.pk, "token": token, "name": instance.name, "created_at": instance.created_at}

        return Response(data, status=status.HTTP_201_CREATED)
