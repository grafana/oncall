from django.apps import apps
from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import (
    MODIFY_ACTIONS,
    READ_ACTIONS,
    ActionPermission,
    AnyRole,
    IsAdminOrEditor,
    IsOwnerOrAdmin,
)
from apps.api.serializers.user_notification_policy import (
    UserNotificationPolicySerializer,
    UserNotificationPolicyUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import BUILT_IN_BACKENDS, NotificationChannelAPIOptions
from apps.user_management.models import User
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import UpdateSerializerMixin


class UserNotificationPolicyView(UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdminOrEditor: (*MODIFY_ACTIONS, "move_to_position"),
        AnyRole: (*READ_ACTIONS, "delay_options", "notify_by_options"),
    }
    action_object_permissions = {
        IsOwnerOrAdmin: (*MODIFY_ACTIONS, "move_to_position"),
        AnyRole: READ_ACTIONS,
    }

    ownership_field = "user"

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
            queryset = self.model.objects.get_or_create_for_user(user=self.request.user, important=important)
        else:
            try:
                target_user = User.objects.get(public_primary_key=user_id)
            except User.DoesNotExist:
                raise BadRequest(detail="User does not exist")

            queryset = self.model.objects.get_or_create_for_user(user=target_user, important=important)

        queryset = self.serializer_class.setup_eager_loading(queryset)

        return queryset.order_by("order")

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
        organization = self.request.auth.organization
        user = serializer.validated_data.get("user") or self.request.user
        old_state = user.repr_settings_for_client_side_logging
        serializer.save()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            self.request.user,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = serializer.validated_data.get("user") or self.request.user
        old_state = user.repr_settings_for_client_side_logging
        serializer.save()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            self.request.user,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = instance.user
        old_state = user.repr_settings_for_client_side_logging
        instance.delete()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            self.request.user,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )

    @action(detail=True, methods=["put"])
    def move_to_position(self, request, pk):
        position = request.query_params.get("position", None)
        if position is not None:
            step = self.get_object()
            try:
                step.to(int(position))
                return Response(status=status.HTTP_200_OK)
            except ValueError as e:
                raise BadRequest(detail=f"{e}")
        else:
            raise BadRequest(detail="Position was not provided")

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
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        choices = []
        for notification_channel in NotificationChannelAPIOptions.AVAILABLE_FOR_USE:
            slack_integration_required = (
                notification_channel in NotificationChannelAPIOptions.SLACK_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            telegram_integration_required = (
                notification_channel
                in NotificationChannelAPIOptions.TELEGRAM_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            email_integration_required = (
                notification_channel in NotificationChannelAPIOptions.EMAIL_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            mobile_app_integration_required = (
                notification_channel
                in NotificationChannelAPIOptions.MOBILE_APP_INTEGRATION_REQUIRED_NOTIFICATION_CHANNELS
            )
            if slack_integration_required and not settings.FEATURE_SLACK_INTEGRATION_ENABLED:
                continue
            if telegram_integration_required and not settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
                continue
            if email_integration_required and not settings.FEATURE_EMAIL_INTEGRATION_ENABLED:
                continue
            if mobile_app_integration_required and not settings.MOBILE_APP_PUSH_NOTIFICATIONS_ENABLED:
                continue

            # extra backends may be enabled per organization
            if notification_channel.name not in BUILT_IN_BACKENDS:
                extra_messaging_backend = get_messaging_backend_from_id(notification_channel.name)
                if extra_messaging_backend is None:
                    continue

            mobile_app_settings = DynamicSetting.objects.get_or_create(
                name="mobile_app_settings",
                defaults={
                    "json_value": {
                        "org_ids": [],
                    }
                },
            )[0]
            if (
                mobile_app_integration_required
                and settings.MOBILE_APP_PUSH_NOTIFICATIONS_ENABLED
                and self.request.auth.organization.pk not in mobile_app_settings.json_value["org_ids"]
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
