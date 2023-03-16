from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.serializers.team import TeamSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Team
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class TeamViewSet(PublicPrimaryKeyMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    serializer_class = TeamSerializer

    def get_queryset(self):
        return self.request.user.available_teams()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        general_team = Team(public_primary_key="null", name="no team", email=None, avatar_url=None)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer([general_team] + list(page), many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer([general_team] + list(queryset), many=True)
        return Response(serializer.data)
