from urllib.parse import urljoin

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudOrganizationConnector, CloudUserIdentity
from apps.user_management.models import User
from common.api_helpers.paginators import HundredPageSizePaginator


class CloudUsersView(HundredPageSizePaginator, APIView):
    authentication_classes = (PluginAuthentication,)
    # TODO: Grafana CN - permissions, ratelimit
    permission_classes = (IsAuthenticated,)

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
            cloud_identity = cloud_identities.get(user.email, None)
            link = None
            status = 0
            if cloud_identity:
                status = 1
                is_phone_verified = cloud_identity.phone_number_verified
                if is_phone_verified:
                    status = 2
                link = urljoin(
                    connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_identity.cloud_id}"
                )

            # TODO: Grafana CN - decide if emails is needed. If yes - don't forget to check that they mustn't be shown to users
            response.append(
                {"id": user.public_primary_key, "username": user.username, "cloud_sync_status": status, "link": link}
            )

        return self.get_paginated_response(response)
