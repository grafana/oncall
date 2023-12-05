from django.core.exceptions import ObjectDoesNotExist
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet as BaseFCMDeviceAuthorizedViewSet
from fcm_django.settings import FCM_DJANGO_SETTINGS as SETTINGS
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mobile_app.auth import MobileAppAuthTokenAuthentication, MobileAppVerificationTokenAuthentication
from apps.mobile_app.models import FCMDevice, MobileAppAuthToken, MobileAppUserSettings
from apps.mobile_app.serializers import FCMDeviceSerializer, MobileAppUserSettingsSerializer


class FCMDeviceAuthorizedViewSet(BaseFCMDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
    serializer_class = FCMDeviceSerializer
    model = FCMDevice

    def create(self, request, *args, **kwargs):
        """Overrides `create` from BaseFCMDeviceAuthorizedViewSet to add filtering by user on getting instance"""
        serializer = None
        is_update = False
        if SETTINGS.get("UPDATE_ON_DUPLICATE_REG_ID") and "registration_id" in request.data:
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
