from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet as BaseFCMDeviceAuthorizedViewSet
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mobile_app.auth import MobileAppAuthTokenAuthentication, MobileAppVerificationTokenAuthentication
from apps.mobile_app.models import MobileAppAuthToken, MobileAppUserSettings
from apps.mobile_app.serializers import MobileAppUserSettingsSerializer


class FCMDeviceAuthorizedViewSet(BaseFCMDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication,)


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
        data = {"id": instance.pk, "token": token, "created_at": instance.created_at}
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        try:
            token = MobileAppAuthToken.objects.get(user=self.request.user)
            token.delete()
        except MobileAppAuthToken.DoesNotExist:
            raise NotFound

        return Response(status=status.HTTP_204_NO_CONTENT)


class MobileAppUserSettingsAPIView(generics.RetrieveUpdateAPIView):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = MobileAppUserSettingsSerializer

    def get_object(self):
        mobile_app_settings, _ = MobileAppUserSettings.objects.get_or_create(user=self.request.user)
        return mobile_app_settings
