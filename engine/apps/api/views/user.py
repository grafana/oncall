import logging
import typing

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django_filters import rest_framework as filters
from drf_spectacular.plumbing import resolve_type_hint
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import (
    ALL_PERMISSION_CHOICES,
    IsOwnerOrHasRBACPermissions,
    LegacyAccessControlRole,
    RBACPermission,
    get_permission_from_permission_string,
    user_is_authorized,
)
from apps.api.serializers.team import TeamSerializer
from apps.api.serializers.user import (
    CurrentUserSerializer,
    FilterUserSerializer,
    ListUserSerializer,
    UserHiddenFieldsSerializer,
    UserIsCurrentlyOnCallSerializer,
    UserSerializer,
)
from apps.api.throttlers import (
    GetPhoneVerificationCodeThrottlerPerOrg,
    GetPhoneVerificationCodeThrottlerPerUser,
    TestCallThrottler,
    VerifyPhoneNumberThrottlerPerOrg,
    VerifyPhoneNumberThrottlerPerUser,
)
from apps.api.throttlers.test_call_throttler import TestPushThrottler
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import UserScheduleExportAuthToken
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.utils import live_settings
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.mobile_app.demo_push import send_test_push
from apps.mobile_app.exceptions import DeviceNotSet
from apps.phone_notifications.exceptions import (
    BaseFailed,
    FailedToFinishVerification,
    FailedToMakeCall,
    FailedToStartVerification,
    NumberAlreadyVerified,
    NumberNotVerified,
    ProviderNotSupports,
)
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.schedules.ical_utils import get_cached_oncall_users_for_multiple_schedules
from apps.schedules.models import OnCallSchedule
from apps.schedules.models.on_call_schedule import ScheduleEvent
from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramVerificationCode
from apps.user_management.models import Team, User
from common.api_helpers.exceptions import Conflict
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import HundredPageSizePaginator
from common.api_helpers.utils import create_engine_url
from common.insight_log import (
    ChatOpsEvent,
    ChatOpsTypePlug,
    EntityEvent,
    write_chatops_insight_log,
    write_resource_insight_log,
)
from common.recaptcha import check_recaptcha_internal_api

logger = logging.getLogger(__name__)
IsOwnerOrHasUserSettingsAdminPermission = IsOwnerOrHasRBACPermissions([RBACPermission.Permissions.USER_SETTINGS_ADMIN])
IsOwnerOrHasUserSettingsReadPermission = IsOwnerOrHasRBACPermissions([RBACPermission.Permissions.USER_SETTINGS_READ])


UPCOMING_SHIFTS_DEFAULT_DAYS = 7
UPCOMING_SHIFTS_MAX_DAYS = 65


class UpcomingShift(typing.TypedDict):
    schedule_id: str
    schedule_name: str
    is_oncall: bool
    current_shift: ScheduleEvent | None
    next_shift: ScheduleEvent | None


UpcomingShifts = list[UpcomingShift]


class CachedSchedulesContextMixin:
    @cached_property
    def schedules_with_oncall_users(self):
        """
        The result of this method is cached and is reused for the whole lifetime of a request,
        since self.get_serializer_context() is called multiple times for every instance in the queryset.
        """
        return get_cached_oncall_users_for_multiple_schedules(self.request.user.organization.oncall_schedules.all())

    def _populate_schedules_oncall_cache(self):
        return False

    def get_serializer_context(self):
        context = getattr(super(), "get_serializer_context", lambda: {})()
        context.update(
            {
                "schedules_with_oncall_users": self.schedules_with_oncall_users
                if self._populate_schedules_oncall_cache()
                else {}
            }
        )
        return context


class CurrentUserView(APIView, CachedSchedulesContextMixin):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
    permission_classes = (IsAuthenticated,)

    def _populate_schedules_oncall_cache(self):
        return True

    def get(self, request):
        context = self.get_serializer_context()
        context.update({"request": self.request, "format": self.format_kwarg, "view": self})

        is_open_source_with_cloud_notifications = (
            settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED
        )
        # set context to avoid additional requests to db
        context["is_open_source_with_cloud_notifications"] = is_open_source_with_cloud_notifications

        if is_open_source_with_cloud_notifications:
            from apps.oss_installation.models import CloudConnector, CloudUserIdentity

            connector = CloudConnector.objects.first()
            if connector is not None:
                cloud_identities = list(CloudUserIdentity.objects.filter(email__in=[request.user.email]))
                cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}
                context["cloud_identities"] = cloud_identities
                context["connector"] = connector

        serializer = CurrentUserSerializer(request.user, context=context)
        return Response(serializer.data)

    def put(self, request):
        context = self.get_serializer_context()
        context.update({"request": self.request})
        data = self.request.data
        serializer = CurrentUserSerializer(request.user, data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    """
    https://django-filter.readthedocs.io/en/master/guide/rest_framework.html
    """

    email = filters.CharFilter(field_name="email", lookup_expr="icontains")
    # TODO: remove "roles" in next version
    roles = filters.MultipleChoiceFilter(field_name="role", choices=LegacyAccessControlRole.choices())
    permission = filters.ChoiceFilter(method="filter_by_permission", choices=ALL_PERMISSION_CHOICES)
    team = TeamModelMultipleChoiceFilter(field_name="teams")

    class Meta:
        model = User
        # TODO: remove "roles" in next version
        fields = ["email", "roles", "permission"]

    def filter_by_permission(self, queryset, name, value):
        rbac_permission = get_permission_from_permission_string(value)
        if not rbac_permission:
            # TODO: maybe raise a 400 here?
            return queryset

        return queryset.filter(
            **User.build_permissions_query(rbac_permission, self.request.user.organization),
        )


class UserView(
    PublicPrimaryKeyMixin[User],
    CachedSchedulesContextMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Internal API endpoints for users.
    """

    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )

    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "retrieve": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "timezone_options": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "check_availability": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "metadata": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "list": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "update": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "partial_update": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "verify_number": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "forget_number": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "get_verification_code": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "get_verification_call": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "get_backend_verification_code": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "get_telegram_verification_code": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "unlink_slack": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "unlink_telegram": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "unlink_backend": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "make_test_call": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "send_test_push": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "send_test_sms": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "export_token": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
        "upcoming_shifts": [RBACPermission.Permissions.USER_SETTINGS_READ],
    }

    rbac_object_permissions = {
        IsOwnerOrHasUserSettingsAdminPermission: [
            "metadata",
            "list",
            "update",
            "partial_update",
            "destroy",
            "verify_number",
            "forget_number",
            "get_verification_code",
            "get_verification_call",
            "get_backend_verification_code",
            "get_telegram_verification_code",
            "unlink_slack",
            "unlink_telegram",
            "unlink_backend",
            "make_test_call",
            "send_test_sms",
            "send_test_push",
            "export_token",
            "upcoming_shifts",
        ],
        IsOwnerOrHasUserSettingsReadPermission: [
            "check_availability",
            "retrieve",
        ],
    }

    queryset = User.objects.none()  # needed for drf-spectacular introspection

    pagination_class = HundredPageSizePaginator

    filter_backends = (SearchFilter, filters.DjangoFilterBackend)
    # NB start search params
    # '^' Starts-with search.
    # '=' Exact matches.
    # '@' Full-text search. (Currently only supported Django's MySQL backend.)
    # '$' Regex search.
    search_fields = (
        "^email",
        "^username",
        "^slack_user_identity__cached_slack_login",
        "^slack_user_identity__cached_name",
        "^teams__name",
        "=public_primary_key",
    )

    filterset_class = UserFilter

    def _get_is_currently_oncall_query_param(self) -> str:
        return self.request.query_params.get("is_currently_oncall", "").lower()

    def _populate_schedules_oncall_cache(self):
        return (
            # admin or owner can see on-call schedule information for a user
            (self.is_owner_or_admin() and self.action != "list")
            or
            # list requests need to explicitly request on-call information
            self._get_is_currently_oncall_query_param() in ["true", "false", "all"]
        )

    def is_owner_or_admin(self):
        request = self.request
        user = request.user
        kwargs = self.kwargs

        is_users_own_data = kwargs.get("pk") is not None and kwargs.get("pk") == user.public_primary_key
        has_admin_permission = user_is_authorized(user, [RBACPermission.Permissions.USER_SETTINGS_ADMIN])

        return is_users_own_data or has_admin_permission

    def get_serializer_class(self):
        request = self.request
        query_params = request.query_params

        is_list_request = self.action == "list"
        is_filters_request = query_params.get("filters", "false") == "true"
        is_owner_or_admin = self.is_owner_or_admin()

        # default serializer
        serializer = UserHiddenFieldsSerializer

        # list requests
        if is_list_request:
            if is_owner_or_admin:
                serializer = ListUserSerializer
            if is_filters_request:
                serializer = FilterUserSerializer
            elif self._populate_schedules_oncall_cache():
                serializer = UserIsCurrentlyOnCallSerializer
            return serializer

        # non-list requests
        if is_owner_or_admin:
            serializer = UserSerializer

        return serializer

    def get_queryset(self):
        slack_identity = self.request.query_params.get("slack_identity", None) == "true"

        queryset = User.objects.filter(organization=self.request.user.organization)

        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        if slack_identity:
            queryset = queryset.filter(slack_user_identity__isnull=False).distinct()

        return queryset.order_by("id")

    @extend_schema(
        responses=PolymorphicProxySerializer(
            component_name="UserPolymorphic",
            serializers=[FilterUserSerializer, UserIsCurrentlyOnCallSerializer, ListUserSerializer],
            resource_type_field_name=None,
        )
    )
    def list(self, request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())

        def _get_oncall_user_ids():
            return {user.pk for _, users in self.schedules_with_oncall_users.items() for user in users}

        paginate_results = True

        if (is_currently_oncall_query_param := self._get_is_currently_oncall_query_param()) == "true":
            # client explicitly wants to filter out users that are on-call
            queryset = queryset.filter(pk__in=_get_oncall_user_ids())
        elif is_currently_oncall_query_param == "false":
            # user explicitly wants to filter out on-call users
            queryset = queryset.exclude(pk__in=_get_oncall_user_ids())
        elif is_currently_oncall_query_param == "all":
            # return all users, don't paginate
            paginate_results = False

        context = self.get_serializer_context()

        if paginate_results and (page := self.paginate_queryset(queryset)) is not None:
            is_open_source_with_cloud_notifications = (
                settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED
            )
            # set context to avoid additional requests to db
            context["is_open_source_with_cloud_notifications"] = is_open_source_with_cloud_notifications

            if is_open_source_with_cloud_notifications:
                from apps.oss_installation.models import CloudConnector, CloudUserIdentity

                if (connector := CloudConnector.objects.first()) is not None:
                    emails = list(queryset.values_list("email", flat=True))
                    cloud_identities = list(CloudUserIdentity.objects.filter(email__in=emails))
                    cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}
                    context["cloud_identities"] = cloud_identities
                    context["connector"] = connector

            serializer = self.get_serializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response(serializer.data)

    @extend_schema(responses=UserSerializer)
    def retrieve(self, request, *args, **kwargs) -> Response:
        context = self.get_serializer_context()

        try:
            instance = self.get_object()
        except NotFound:
            return self.wrong_team_response()

        is_open_source_with_cloud_notifications = (
            settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED
        )
        # set context to avoid additional requests to db
        context["is_open_source_with_cloud_notifications"] = is_open_source_with_cloud_notifications

        if is_open_source_with_cloud_notifications:
            from apps.oss_installation.models import CloudConnector, CloudUserIdentity

            connector = CloudConnector.objects.first()
            if connector is not None:
                cloud_identities = list(CloudUserIdentity.objects.filter(email__in=[instance.email]))
                cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}
                context["cloud_identities"] = cloud_identities
                context["connector"] = connector

        serializer = self.get_serializer(instance, context=context)
        return Response(serializer.data)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def wrong_team_response(self) -> Response:
        """
        This method returns 403 and {"error_code": "wrong_team", "owner_team": {"name", "id", "email", "avatar_url"}}.
        Used in case if a requested instance doesn't belong to user's current_team.
        Used instead of TeamFilteringMixin because of m2m teams field (mixin doesn't work correctly with this)
        and overridden retrieve method in UserView.
        """
        queryset = User.objects.filter(organization=self.request.user.organization).order_by("id")
        queryset = self.filter_queryset(queryset)

        try:
            queryset.get(public_primary_key=self.kwargs["pk"])
        except ObjectDoesNotExist:
            raise NotFound

        general_team = Team(public_primary_key=None, name="General", email=None, avatar_url=None)

        return Response(
            data={"error_code": "wrong_team", "owner_team": TeamSerializer(general_team).data},
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(responses={status.HTTP_200_OK: resolve_type_hint(typing.List[str])})
    @action(detail=False, methods=["get"])
    def timezone_options(self, request) -> Response:
        return Response(pytz.common_timezones)

    @action(
        detail=True,
        methods=["get"],
        throttle_classes=[GetPhoneVerificationCodeThrottlerPerUser, GetPhoneVerificationCodeThrottlerPerOrg],
    )
    def get_verification_code(self, request, pk) -> Response:
        logger.info("get_verification_code: validating reCAPTCHA code")
        valid = check_recaptcha_internal_api(request, "mobile_verification_code")
        if not valid:
            logger.warning("get_verification_code: invalid reCAPTCHA validation")
            return Response("failed reCAPTCHA check", status=status.HTTP_400_BAD_REQUEST)
        logger.info('get_verification_code: pass reCAPTCHA validation"')

        user = self.get_object()
        phone_backend = PhoneBackend()
        try:
            phone_backend.send_verification_sms(user)
        except NumberAlreadyVerified:
            return Response("Phone number already verified", status=status.HTTP_400_BAD_REQUEST)
        except FailedToStartVerification as e:
            return handle_phone_notificator_failed(e)
        except ProviderNotSupports:
            return Response(
                "Phone provider not supports sms verification", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        throttle_classes=[GetPhoneVerificationCodeThrottlerPerUser, GetPhoneVerificationCodeThrottlerPerOrg],
    )
    def get_verification_call(self, request, pk) -> Response:
        logger.info("get_verification_code_via_call: validating reCAPTCHA code")
        valid = check_recaptcha_internal_api(request, "mobile_verification_code")
        if not valid:
            logger.warning("get_verification_code_via_call: invalid reCAPTCHA validation")
            return Response("failed reCAPTCHA check", status=status.HTTP_400_BAD_REQUEST)
        logger.info('get_verification_code_via_call: pass reCAPTCHA validation"')

        user = self.get_object()
        phone_backend = PhoneBackend()
        try:
            phone_backend.make_verification_call(user)
        except NumberAlreadyVerified:
            return Response("Phone number already verified", status=status.HTTP_400_BAD_REQUEST)
        except FailedToStartVerification as e:
            return handle_phone_notificator_failed(e)
        except ProviderNotSupports:
            return Response(
                "Phone provider not supports call verification", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(status=status.HTTP_200_OK)

    @extend_schema(parameters=[inline_serializer(name="UserVerifyNumber", fields={"token": serializers.CharField()})])
    @action(
        detail=True,
        methods=["put"],
        throttle_classes=[VerifyPhoneNumberThrottlerPerUser, VerifyPhoneNumberThrottlerPerOrg],
    )
    def verify_number(self, request, pk) -> Response:
        target_user = self.get_object()
        code = request.query_params.get("token", None)
        if not code:
            return Response("Invalid verification code", status=status.HTTP_400_BAD_REQUEST)
        prev_state = target_user.insight_logs_serialized

        phone_backend = PhoneBackend()
        try:
            verified = phone_backend.verify_phone_number(target_user, code)
        except FailedToFinishVerification as e:
            return handle_phone_notificator_failed(e)
        if verified:
            new_state = target_user.insight_logs_serialized
            write_resource_insight_log(
                instance=target_user,
                author=self.request.user,
                event=EntityEvent.UPDATED,
                prev_state=prev_state,
                new_state=new_state,
            )
            return Response(status=status.HTTP_200_OK)
        else:
            return Response("Verification code is not correct", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["put"])
    def forget_number(self, request, pk) -> Response:
        target_user = self.get_object()
        prev_state = target_user.insight_logs_serialized

        phone_backend = PhoneBackend()
        removed = phone_backend.forget_number(target_user)

        if removed:
            new_state = target_user.insight_logs_serialized
            write_resource_insight_log(
                instance=target_user,
                author=self.request.user,
                event=EntityEvent.UPDATED,
                prev_state=prev_state,
                new_state=new_state,
            )
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], throttle_classes=[TestCallThrottler])
    def make_test_call(self, request, pk) -> Response:
        user = self.get_object()
        try:
            phone_backend = PhoneBackend()
            phone_backend.make_test_call(user)
        except NumberNotVerified:
            return Response("Phone number is not verified", status=status.HTTP_400_BAD_REQUEST)
        except FailedToMakeCall as e:
            return handle_phone_notificator_failed(e)
        except ProviderNotSupports:
            return Response("Phone provider not supports phone calls", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], throttle_classes=[TestCallThrottler])
    def send_test_sms(self, request, pk) -> Response:
        user = self.get_object()
        try:
            phone_backend = PhoneBackend()
            phone_backend.send_test_sms(user)
        except NumberNotVerified:
            return Response("Phone number is not verified", status=status.HTTP_400_BAD_REQUEST)
        except FailedToMakeCall as e:
            return handle_phone_notificator_failed(e)
        except ProviderNotSupports:
            return Response("Phone provider not supports phone calls", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            inline_serializer(
                name="UserSendTestPush", fields={"critical": serializers.BooleanField(required=False, default=False)}
            )
        ]
    )
    @action(detail=True, methods=["post"], throttle_classes=[TestPushThrottler])
    def send_test_push(self, request, pk) -> Response:
        user = self.get_object()
        critical = request.query_params.get("critical", "false") == "true"

        try:
            send_test_push(user, critical)
        except DeviceNotSet:
            return Response(
                data="Mobile device not connected",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.info(f"UserView.send_test_push: Unable to send test push due to {e}")
            return Response(
                data="Something went wrong while sending a test push", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            inline_serializer(name="UserGetBackendVerificationCode", fields={"backend": serializers.CharField()})
        ]
    )
    @action(detail=True, methods=["get"])
    def get_backend_verification_code(self, request, pk) -> Response:
        user = self.get_object()

        backend_id = request.query_params.get("backend")
        backend = get_messaging_backend_from_id(backend_id)
        if backend is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        code = backend.generate_user_verification_code(user)
        return Response(code)

    @extend_schema(
        responses=inline_serializer(
            name="UserGetTelegramVerificationCode",
            fields={
                "telegram_code": serializers.CharField(),
                "bot_link": serializers.CharField(),
            },
        )
    )
    @action(detail=True, methods=["get"])
    def get_telegram_verification_code(self, request, pk) -> Response:
        user = self.get_object()

        if user.is_telegram_connected:
            return Response("This user is already connected to a Telegram account", status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_verification_code = user.telegram_verification_code
            existing_verification_code.delete()
        except TelegramVerificationCode.DoesNotExist:
            pass

        new_code = TelegramVerificationCode(user=user)
        new_code.save()

        telegram_client = TelegramClient()
        bot_username = telegram_client.api_client.username
        bot_link = f"https://t.me/{bot_username}"

        return Response(
            {"telegram_code": str(new_code.uuid_with_org_uuid), "bot_link": bot_link}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def unlink_slack(self, request, pk) -> Response:
        user = self.get_object()
        user.slack_user_identity = None
        user.save(update_fields=["slack_user_identity"])
        write_chatops_insight_log(
            author=request.user,
            event_name=ChatOpsEvent.USER_UNLINKED,
            chatops_type=ChatOpsTypePlug.SLACK.value,
            linked_user=user.username,
            linked_user_id=user.public_primary_key,
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unlink_telegram(self, request, pk) -> Response:
        user = self.get_object()
        from apps.telegram.models import TelegramToUserConnector

        try:
            connector = TelegramToUserConnector.objects.get(user=user)
            connector.delete()
            write_chatops_insight_log(
                author=request.user,
                event_name=ChatOpsEvent.USER_UNLINKED,
                chatops_type=ChatOpsTypePlug.TELEGRAM.value,
                linked_user=user.username,
                linked_user_id=user.public_primary_key,
            )
        except TelegramToUserConnector.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[inline_serializer(name="UserUnlinkBackend", fields={"backend": serializers.CharField()})]
    )
    @action(detail=True, methods=["post"])
    def unlink_backend(self, request, pk) -> Response:
        # TODO: insight logs support
        user = self.get_object()

        backend_id = request.query_params.get("backend")
        backend = get_messaging_backend_from_id(backend_id)
        if backend is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            backend.unlink_user(user)
            write_chatops_insight_log(
                author=request.user,
                event_name=ChatOpsEvent.USER_UNLINKED,
                chatops_type=backend.backend_id,
                linked_user=user.username,
                linked_user_id=user.public_primary_key,
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            inline_serializer(
                name="UserUpcomingShiftsParams",
                fields={"days": serializers.IntegerField(required=False, default=UPCOMING_SHIFTS_DEFAULT_DAYS)},
            )
        ],
        responses={status.HTTP_200_OK: resolve_type_hint(UpcomingShifts)},
    )
    @action(detail=True, methods=["get"])
    def upcoming_shifts(self, request, pk) -> Response:
        user = self.get_object()
        try:
            days = int(request.query_params.get("days", UPCOMING_SHIFTS_DEFAULT_DAYS))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if days <= 0 or days > UPCOMING_SHIFTS_MAX_DAYS:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        # filter user-related schedules
        schedules = OnCallSchedule.objects.related_to_user(user)

        # check upcoming shifts
        upcoming = []
        for schedule in schedules:
            _, current_shifts, upcoming_shifts = schedule.shifts_for_user(user, datetime_start=now, days=days)
            if current_shifts or upcoming_shifts:
                upcoming.append(
                    {
                        "schedule_id": schedule.public_primary_key,
                        "schedule_name": schedule.name,
                        "is_oncall": len(current_shifts) > 0,
                        "current_shift": current_shifts[0] if current_shifts else None,
                        "next_shift": upcoming_shifts[0] if upcoming_shifts else None,
                        "upcoming_shifts": upcoming_shifts or None,
                    }
                )

        # sort entries by start timestamp
        def sorting_key(entry):
            shift = entry["current_shift"] if entry["current_shift"] else entry["next_shift"]
            return shift["start"]

        upcoming.sort(key=sorting_key)

        return Response(upcoming, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["get"],
        responses=inline_serializer(
            name="UserExportTokenGetResponse",
            fields={
                "created_at": serializers.DateTimeField(),
                "revoked_at": serializers.DateTimeField(allow_null=True),
                "active": serializers.BooleanField(),
            },
        ),
    )
    @extend_schema(
        methods=["post"],
        responses=inline_serializer(
            name="UserExportTokenPostResponse",
            fields={
                "token": serializers.CharField(),
                "created_at": serializers.DateTimeField(),
                "export_url": serializers.CharField(),
            },
        ),
    )
    @action(detail=True, methods=["get", "post", "delete"])
    def export_token(self, request, pk) -> Response:
        user = self.get_object()

        if self.request.method == "GET":
            try:
                token = UserScheduleExportAuthToken.objects.get(user=user)
            except UserScheduleExportAuthToken.DoesNotExist:
                raise NotFound

            response = {
                "created_at": token.created_at,
                "revoked_at": token.revoked_at,
                "active": token.active,
            }
            return Response(response, status=status.HTTP_200_OK)

        if self.request.method == "POST":
            try:
                instance, token = UserScheduleExportAuthToken.create_auth_token(user, user.organization)
                write_resource_insight_log(instance=instance, author=self.request.user, event=EntityEvent.CREATED)
            except IntegrityError:
                raise Conflict("Schedule export token for user already exists")

            export_url = create_engine_url(
                reverse("api-public:users-schedule-export", kwargs={"pk": user.public_primary_key})
                + f"?{SCHEDULE_EXPORT_TOKEN_NAME}={token}"
            )

            data = {"token": token, "created_at": instance.created_at, "export_url": export_url}
            return Response(data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            try:
                token = UserScheduleExportAuthToken.objects.get(user=user)
                write_resource_insight_log(instance=token, author=self.request.user, event=EntityEvent.DELETED)
                token.delete()
            except UserScheduleExportAuthToken.DoesNotExist:
                raise NotFound
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def handle_phone_notificator_failed(exc: BaseFailed) -> Response:
    if exc.graceful_msg:
        return Response(exc.graceful_msg, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Something went wrong", status=status.HTTP_503_SERVICE_UNAVAILABLE)
