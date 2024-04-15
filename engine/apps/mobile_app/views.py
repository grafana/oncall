import enum
import logging
import typing

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet as BaseFCMDeviceAuthorizedViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mobile_app.auth import MobileAppAuthTokenAuthentication, MobileAppVerificationTokenAuthentication
from apps.mobile_app.models import FCMDevice, MobileAppAuthToken, MobileAppUserSettings
from apps.mobile_app.serializers import FCMDeviceSerializer, MobileAppUserSettingsSerializer
from common.cloud_auth_api.client import CloudAuthApiClient, CloudAuthApiException

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization, User


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FCMDeviceAuthorizedViewSet(BaseFCMDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
    serializer_class = FCMDeviceSerializer
    model = FCMDevice

    def create(self, request, *args, **kwargs):
        """Overrides `create` from BaseFCMDeviceAuthorizedViewSet to add filtering by user on getting instance"""
        serializer = None
        is_update = False
        if settings.FCM_DJANGO_SETTINGS["UPDATE_ON_DUPLICATE_REG_ID"] and "registration_id" in request.data:
            instance = self.model.objects.filter(
                registration_id=request.data["registration_id"], user=self.request.user
            ).first()
            if instance:
                serializer = self.get_serializer(instance, data=request.data)
                is_update = True
        if not serializer:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        if is_update:
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_object(self):
        """Overrides original method to add filtering by user"""
        try:
            obj = self.model.objects.get(registration_id=self.kwargs["registration_id"], user=self.request.user)
        except ObjectDoesNotExist:
            raise NotFound
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class MobileAppAuthTokenAPIView(APIView):
    authentication_classes = (MobileAppVerificationTokenAuthentication,)

    def get(self, request):
        try:
            token = MobileAppAuthToken.objects.get(user=self.request.user)
        except MobileAppAuthToken.DoesNotExist:
            raise NotFound

        response = {
            "token_id": token.id,
            "user_id": token.user_id,
            "organization_id": token.organization_id,
            "created_at": token.created_at,
            "revoked_at": token.revoked_at,
            "stack_slug": self.request.auth.organization.stack_slug,
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        # If token already exists revoke it
        try:
            token = MobileAppAuthToken.objects.get(user=self.request.user)
            token.delete()
        except MobileAppAuthToken.DoesNotExist:
            pass

        instance, token = MobileAppAuthToken.create_auth_token(self.request.user, self.request.user.organization)
        data = {
            "id": instance.pk,
            "token": token,
            "created_at": instance.created_at,
            "stack_slug": self.request.auth.organization.stack_slug,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        try:
            token = MobileAppAuthToken.objects.get(user=self.request.user)
            token.delete()
        except MobileAppAuthToken.DoesNotExist:
            raise NotFound

        return Response(status=status.HTTP_204_NO_CONTENT)


class MobileAppUserSettingsViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = MobileAppUserSettingsSerializer

    def get_object(self):
        mobile_app_settings, _ = MobileAppUserSettings.objects.get_or_create(user=self.request.user)
        return mobile_app_settings

    def notification_timing_options(self, request):
        choices = [
            {"value": item[0], "display_name": item[1]} for item in MobileAppUserSettings.NOTIFICATION_TIMING_CHOICES
        ]
        return Response(choices)


class MobileAppGatewayView(APIView):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    class SupportedDownstreamBackends(enum.StrEnum):
        INCIDENT = "incident"

    ALL_SUPPORTED_DOWNSTREAM_BACKENDS = list(SupportedDownstreamBackends)

    def initial(self, request: Request, *args, **kwargs):
        # If the mobile app gateway is not enabled, return a 404
        if not settings.MOBILE_APP_GATEWAY_ENABLED:
            raise NotFound
        super().initial(request, *args, **kwargs)

    @classmethod
    def _get_auth_token(cls, downstream_backend: SupportedDownstreamBackends, user: "User") -> str:
        """
        RS256 = asymmetric = public/private key pair
        HS256 = symmetric = shared secret (don't use this)
        """
        org = user.organization
        token_scopes = {
            cls.SupportedDownstreamBackends.INCIDENT: [CloudAuthApiClient.Scopes.INCIDENT_WRITE],
        }[downstream_backend]

        return f"{org.stack_id}:{CloudAuthApiClient().request_signed_token(user, token_scopes)}"

    @classmethod
    def _get_downstream_headers(
        cls, request: Request, downstream_backend: SupportedDownstreamBackends, user: "User"
    ) -> typing.Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {cls._get_auth_token(downstream_backend, user)}",
        }

        if (v := request.META.get("CONTENT_TYPE", None)) is not None:
            headers["Content-Type"] = v

        return headers

    @classmethod
    def _get_downstream_url(
        cls, organization: "Organization", downstream_backend: SupportedDownstreamBackends, downstream_path: str
    ) -> str:
        downstream_url = {
            cls.SupportedDownstreamBackends.INCIDENT: organization.grafana_incident_backend_url,
        }[downstream_backend]

        if downstream_url is None:
            raise ParseError(
                f"Downstream URL not found for backend {downstream_backend} for organization {organization.pk}"
            )

        return f"{downstream_url}/{downstream_path}"

    def _proxy_request(self, request: Request, *args, **kwargs) -> Response:
        downstream_backend = kwargs["downstream_backend"]
        downstream_path = kwargs["downstream_path"]
        method = request.method
        user = request.user

        if downstream_backend not in self.ALL_SUPPORTED_DOWNSTREAM_BACKENDS:
            raise NotFound(f"Downstream backend {downstream_backend} not supported")

        downstream_url = self._get_downstream_url(user.organization, downstream_backend, downstream_path)

        log_msg_common = f"{downstream_backend} request to {method} {downstream_url}"
        logger.info(f"Proxying {log_msg_common}")

        downstream_request_handler = getattr(requests, method.lower())

        try:
            downstream_response = downstream_request_handler(
                downstream_url,
                data=request.body,
                params=request.query_params.dict(),
                headers=self._get_downstream_headers(request, downstream_backend, user),
            )

            logger.info(f"Successfully proxied {log_msg_common}")
            return Response(status=downstream_response.status_code, data=downstream_response.json())
        except (
            requests.exceptions.RequestException,
            requests.exceptions.JSONDecodeError,
            CloudAuthApiException,
        ) as e:
            if isinstance(e, requests.exceptions.JSONDecodeError):
                final_status = status.HTTP_400_BAD_REQUEST
            else:
                final_status = status.HTTP_502_BAD_GATEWAY

            logger.error(
                (
                    f"MobileAppGatewayView: error while proxying request\n"
                    f"method={method}\n"
                    f"downstream_backend={downstream_backend}\n"
                    f"downstream_path={downstream_path}\n"
                    f"downstream_url={downstream_url}\n"
                    f"final_status={final_status}"
                ),
                exc_info=True,
            )
            return Response(status=final_status)


"""
See the default `APIView.dispatch` for more info. Basically this just routes all requests for
ALL HTTP verbs to the `MobileAppGatewayView._proxy_request` method.
"""
for method in APIView.http_method_names:
    setattr(MobileAppGatewayView, method.lower(), MobileAppGatewayView._proxy_request)
