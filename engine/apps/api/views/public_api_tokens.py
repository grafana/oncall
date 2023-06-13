from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.api.serializers.public_api_token import PublicApiTokenSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import MAX_PUBLIC_API_TOKENS_PER_USER
from apps.auth_token.models import ApiAuthToken
from common.api_helpers.exceptions import BadRequest
from common.insight_log import EntityEvent, write_resource_insight_log


class PublicApiTokenView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [PluginAuthentication]
    permission_classes = [IsAuthenticated, RBACPermission]
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.API_KEYS_READ],
        "list": [RBACPermission.Permissions.API_KEYS_READ],
        "retrieve": [RBACPermission.Permissions.API_KEYS_READ],
        "create": [RBACPermission.Permissions.API_KEYS_WRITE],
        "destroy": [RBACPermission.Permissions.API_KEYS_WRITE],
    }

    model = ApiAuthToken
    serializer_class = PublicApiTokenSerializer

    def get_queryset(self):
        return ApiAuthToken.objects.filter(user=self.request.user, organization=self.request.user.organization)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        write_resource_insight_log(instance=instance, author=request.user, event=EntityEvent.DELETED)
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
        write_resource_insight_log(instance=instance, author=user, event=EntityEvent.CREATED)
        return Response(data, status=status.HTTP_201_CREATED)
