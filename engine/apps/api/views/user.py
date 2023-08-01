import logging

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.urls import reverse
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.paging import check_user_availability
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
    UserHiddenFieldsSerializer,
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
from apps.schedules.models import OnCallSchedule
from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramVerificationCode
from apps.user_management.models import Team, User
from common.api_helpers.exceptions import Conflict
from common.api_helpers.mixins import FilterSerializerMixin, PublicPrimaryKeyMixin
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


class CurrentUserView(APIView):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        context = {"request": self.request, "format": self.format_kwarg, "view": self}

        if settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
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
        data = self.request.data
        serializer = CurrentUserSerializer(request.user, data=data, context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserFilter(filters.FilterSet):
    """
    https://django-filter.readthedocs.io/en/master/guide/rest_framework.html
    """

    email = filters.CharFilter(field_name="email", lookup_expr="icontains")
    # TODO: remove "roles" in next version
    roles = filters.MultipleChoiceFilter(field_name="role", choices=LegacyAccessControlRole.choices())
    permission = filters.ChoiceFilter(method="filter_by_permission", choices=ALL_PERMISSION_CHOICES)

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
    PublicPrimaryKeyMixin,
    FilterSerializerMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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
        "list": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
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
            "retrieve",
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
        ],
    }

    filter_serializer_class = FilterUserSerializer

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
    )

    filterset_class = UserFilter

    def get_serializer_class(self):
        request = self.request
        user = request.user
        kwargs = self.kwargs

        is_filters_request = request.query_params.get("filters", "false") == "true"
        if self.action in ["list"] and is_filters_request:
            return self.get_filter_serializer_class()

        is_users_own_data = kwargs.get("pk") is not None and kwargs.get("pk") == user.public_primary_key
        has_admin_permission = user_is_authorized(user, [RBACPermission.Permissions.USER_SETTINGS_ADMIN])

        if is_users_own_data or has_admin_permission:
            return UserSerializer
        return UserHiddenFieldsSerializer

    def get_queryset(self):
        slack_identity = self.request.query_params.get("slack_identity", None) == "true"

        queryset = User.objects.filter(organization=self.request.user.organization)

        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        if slack_identity:
            queryset = queryset.filter(slack_user_identity__isnull=False).distinct()

        return queryset.order_by("id")

    def list(self, request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            context = {"request": self.request, "format": self.format_kwarg, "view": self}
            if settings.IS_OPEN_SOURCE:
                if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                    from apps.oss_installation.models import CloudConnector, CloudUserIdentity

                    connector = CloudConnector.objects.first()
                    if connector is not None:
                        emails = list(queryset.values_list("email", flat=True))
                        cloud_identities = list(CloudUserIdentity.objects.filter(email__in=emails))
                        cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}
                        context["cloud_identities"] = cloud_identities
                        context["connector"] = connector
            serializer = self.get_serializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs) -> Response:
        context = {"request": self.request, "format": self.format_kwarg, "view": self}
        try:
            instance = self.get_object()
        except NotFound:
            return self.wrong_team_response()

        if settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
            from apps.oss_installation.models import CloudConnector, CloudUserIdentity

            connector = CloudConnector.objects.first()
            if connector is not None:
                cloud_identities = list(CloudUserIdentity.objects.filter(email__in=[instance.email]))
                cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}
                context["cloud_identities"] = cloud_identities
                context["connector"] = connector

        serializer = self.get_serializer(instance, context=context)
        return Response(serializer.data)

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

    def current(self, request) -> Response:
        serializer = UserSerializer(self.get_queryset().get(pk=self.request.user.pk))
        return Response(serializer.data)

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

    @action(detail=True, methods=["get"])
    def get_backend_verification_code(self, request, pk) -> Response:
        user = self.get_object()

        backend_id = request.query_params.get("backend")
        backend = get_messaging_backend_from_id(backend_id)
        if backend is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        code = backend.generate_user_verification_code(user)
        return Response(code)

    @action(detail=True, methods=["get"])
    def get_telegram_verification_code(self, request, pk) -> Response:
        user = self.get_object()

        if not user.is_telegram_connected:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=["get"])
    def upcoming_shifts(self, request, pk) -> Response:
        user = self.get_object()
        try:
            days = int(request.query_params.get("days", UPCOMING_SHIFTS_DEFAULT_DAYS))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if days <= 0 or days > UPCOMING_SHIFTS_MAX_DAYS:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # filter user-related schedules
        schedules = OnCallSchedule.objects.related_to_user(user)

        # check upcoming shifts
        upcoming = []
        for schedule in schedules:
            current_shift, upcoming_shift = schedule.upcoming_shift_for_user(user, days=days)
            if current_shift or upcoming_shift:
                upcoming.append(
                    {
                        "schedule_id": schedule.public_primary_key,
                        "schedule_name": schedule.name,
                        "is_oncall": current_shift is not None,
                        "current_shift": current_shift,
                        "next_shift": upcoming_shift,
                    }
                )

        # sort entries by start timestamp
        def sorting_key(entry):
            shift = entry["current_shift"] if entry["current_shift"] else entry["next_shift"]
            return shift["start"]

        upcoming.sort(key=sorting_key)

        return Response(upcoming, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=["get"])
    def check_availability(self, request, pk) -> Response:
        user = self.get_object()
        warnings = check_user_availability(user=user)
        return Response(data={"warnings": warnings}, status=status.HTTP_200_OK)


def handle_phone_notificator_failed(exc: BaseFailed) -> Response:
    if exc.graceful_msg:
        return Response(exc.graceful_msg, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Something went wrong", status=status.HTTP_503_SERVICE_UNAVAILABLE)
