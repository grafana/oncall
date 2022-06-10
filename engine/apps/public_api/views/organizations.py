from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import OrganizationSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.models import Organization
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import TwentyFivePageSizePaginator


class OrganizationView(
    RateLimitHeadersMixin,
    ReadOnlyModelViewSet,
):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = Organization
    serializer_class = OrganizationSerializer

    pagination_class = TwentyFivePageSizePaginator

    def get_queryset(self):
        # It's a dirty hack to get queryset from the object. Just in case we'll return multiple teams in the future.
        return Organization.objects.filter(pk=self.request.auth.organization.pk)

    def get_object(self):
        return self.request.auth.organization

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}
