from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.base.models import UserNotificationPolicy
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers import PersonalNotificationRuleSerializer, PersonalNotificationRuleUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.models import User
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import DemoTokenMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class PersonalNotificationView(RateLimitHeadersMixin, DemoTokenMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = UserNotificationPolicy
    serializer_class = PersonalNotificationRuleSerializer
    update_serializer_class = PersonalNotificationRuleUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    demo_default_id = public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id", None)
        important = self.request.query_params.get("important", None)
        organization = self.request.auth.organization
        if user_id is not None:
            if user_id != self.request.user.public_primary_key:
                try:
                    User.objects.get(
                        public_primary_key=user_id,
                        organization=organization,
                    )
                except User.DoesNotExist:
                    raise BadRequest(detail="User not found.")
            queryset = UserNotificationPolicy.objects.filter(
                user__public_primary_key=user_id,
                user__organization=organization,
            )
        else:
            queryset = UserNotificationPolicy.objects.filter(user__organization=organization).distinct()
        if important is not None:
            if important == "true":
                queryset = queryset.filter(important=True)
            elif important == "false":
                queryset = queryset.filter(important=False)
            else:
                raise BadRequest(detail="Important is not bool")

        queryset = self.serializer_class.setup_eager_loading(queryset)

        return queryset.order_by("user", "important", "order")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]
        queryset = self.filter_queryset(self.get_queryset())
        try:
            return queryset.get(public_primary_key=public_primary_key)
        except UserNotificationPolicy.DoesNotExist:
            raise NotFound

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = user.repr_settings_for_client_side_logging
        instance.delete()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            user,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )

    def perform_create(self, serializer):
        organization = self.request.auth.organization
        author = self.request.user
        user = serializer.validated_data["user"]

        old_state = user.repr_settings_for_client_side_logging
        serializer.save()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            author,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = user.repr_settings_for_client_side_logging
        serializer.save()
        new_state = user.repr_settings_for_client_side_logging
        description = f"User settings for user {user.username} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization,
            user,
            OrganizationLogType.TYPE_USER_SETTINGS_CHANGED,
            description,
        )
