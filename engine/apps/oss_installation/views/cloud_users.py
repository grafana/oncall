from urllib.parse import urljoin

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

import apps.oss_installation.constants as cloud_constants
from apps.api.permissions import IsAdmin
from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudOrganizationConnector, CloudUserIdentity
from apps.user_management.models import User
from common.api_helpers.paginators import HundredPageSizePaginator


class CloudUsersView(HundredPageSizePaginator, APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        queryset = User.objects.filter(organization=self.request.user.organization)

        if self.request.user.current_team is not None:
            queryset = queryset.filter(teams=self.request.user.current_team).distinct()

        results = self.paginate_queryset(queryset, request, view=self)

        emails = list(queryset.values_list("email", flat=True))
        cloud_identities = list(
            CloudUserIdentity.objects.filter(organization=self.request.user.organization, email__in=emails)
        )
        cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}

        response = []

        connector = CloudOrganizationConnector.objects.first()
        for user in results:
            link = None
            status = cloud_constants.CLOUD_NOT_SYNCED
            if connector is not None:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                cloud_identity = cloud_identities.get(user.email, None)
                if cloud_identity:
                    status = cloud_constants.CLOUD_SYNCED_PHONE_NOT_VERIFIED
                    is_phone_verified = cloud_identity.phone_number_verified
                    if is_phone_verified:
                        status = cloud_constants.CLOUD_SYNCED_PHONE_VERIFIED
                    link = urljoin(
                        connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_identity.cloud_id}"
                    )

            response.append(
                {
                    "id": user.public_primary_key,
                    "email": user.email,
                    "username": user.username,
                    "cloud_data": {"status": status, "link": link},
                }
            )

        return self.get_paginated_response(response)
