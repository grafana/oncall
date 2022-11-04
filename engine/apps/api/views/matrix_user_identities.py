from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.matrix_user_identity import MatrixUserIdentitySerializer
from apps.auth_token.auth import PluginAuthentication
from apps.matrix.models import MatrixUserIdentity

import logging

logger = logging.getLogger(__name__)


class MatrixUserIdentityView(
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    queryset = MatrixUserIdentity.objects.all()

    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "set_default"),
        AnyRole: READ_ACTIONS,
    }

    serializer_class = MatrixUserIdentitySerializer
    update_serializer_class = MatrixUserIdentitySerializer
