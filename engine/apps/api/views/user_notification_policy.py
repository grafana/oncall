from django.conf import settings
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsOwnerOrHasRBACPermissions, RBACPermission
from apps.api.serializers.user_notification_policy import (
    UserNotificationPolicySerializer,
    UserNotificationPolicyUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import BUILT_IN_BACKENDS, NotificationChannelAPIOptions
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import UpdateSerializerMixin
from common.exceptions import UserNotificationPolicyCouldNotBeDeleted
from common.insight_log import EntityEvent, write_resource_insight_log
from common.ordered_model.viewset import OrderedModelViewSet


class UserNotificationPolicyView(UpdateSerializerMixin, OrderedModelViewSet):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "list": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "retrieve": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "delay_options": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "notify_by_options": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "create": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "update": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "partial_update": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "destroy": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "move_to_position": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
    }

    IsOwnerOrHasUserSettingsAdminPermission = IsOwnerOrHasRBACPermissions(
        required_permissions=[RBACPermission.Permissions.USER_SETTINGS_ADMIN], ownership_field="user"
    )

    rbac_object_permissions = {
        IsOwnerOrHasUserSettingsAdminPermission: [
            "create",
            "update",
            "partial_update",
            "destroy",
            "move_to_position",
        ],
    }

    model = UserNotificationPolicy
    serializer_class = UserNotificationPolicySerializer
    update_serializer_class = UserNotificationPolicyUpdateSerializer

    def get_queryset(self):
        important = self.request.query_params.get("important", None) == "true"
        try:
            user_id = self.request.query_params.get("user", None)
        except ValueError:
            raise BadRequest(detail="Invalid user param")
        if user_id is None or user_id == self.request.user.public_primary_key:
            queryset = self.model.objects.filter(user=self.request.user, important=important)
        else:
            try:
                target_user = User.objects.get(public_primary_key=user_id)
            except User.DoesNotExist:
                raise BadRequest(detail="User does not exist")

            queryset = self.model.objects.filter(user=target_user, important=important)

        return self.serializer_class.setup_eager_loading(queryset)

    def get_object(self):
        # we need overriden get object, because original one call get_queryset first and raise 404 trying to access
        # other user policies
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization

        try:
            obj = UserNotificationPolicy.objects.get(public_primary_key=pk, user__organization=organization)
        except UserNotificationPolicy.DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        user = serializer.validated_data.get("user") or self.request.user
        prev_state = user.insight_logs_serialized
        serializer.save()
        new_state = user.insight_logs_serialized
        write_resource_insight_log(
            instance=user,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_update(self, serializer):
        user = serializer.validated_data.get("user") or self.request.user
        prev_state = user.insight_logs_serialized
        serializer.save()
        new_state = user.insight_logs_serialized
        write_resource_insight_log(
            instance=user,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        user = instance.user
        prev_state = user.insight_logs_serialized
        try:
            instance.delete()
        except UserNotificationPolicyCouldNotBeDeleted:
            raise BadRequest(detail="Can't delete last user notification policy")
        new_state = user.insight_logs_serialized
        write_resource_insight_log(
            instance=user,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    @action(detail=False, methods=["get"])
    def delay_options(self, request):
        choices = []
        for item in UserNotificationPolicy.DURATION_CHOICES:
            choices.append({"value": str(item[0]), "sec_value": item[0], "display_name": item[1]})
        return Response(choices)

    @action(detail=False, methods=["get"])
    def notify_by_options(self, request):
        """
        Returns list of options for user notification policies dropping options that requires disabled features.
        """
        choices = []
        for notification_channel in NotificationChannelAPIOptions.AVAILABLE_FOR_USE:
            slack_integration_required = (
                notification_channel in NotificationChannelAPIOptions.SLACK_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            telegram_integration_required = (
                notification_channel
                in NotificationChannelAPIOptions.TELEGRAM_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            if slack_integration_required and not settings.FEATURE_SLACK_INTEGRATION_ENABLED:
                continue
            if telegram_integration_required and not settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
                continue

            # extra backends may be enabled per organization
            built_in_backend_names = {b[0] for b in BUILT_IN_BACKENDS}
            if notification_channel.name not in built_in_backend_names:
                extra_messaging_backend = get_messaging_backend_from_id(notification_channel.name)
                if extra_messaging_backend is None or not extra_messaging_backend.is_enabled_for_organization(
                    request.auth.organization
                ):
                    continue

            choices.append(
                {
                    "value": notification_channel,
                    "display_name": NotificationChannelAPIOptions.LABELS[notification_channel],
                    "slack_integration_required": slack_integration_required,
                    "telegram_integration_required": telegram_integration_required,
                }
            )
        return Response(choices)
