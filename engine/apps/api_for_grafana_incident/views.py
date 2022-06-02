from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.alerts.models import AlertGroup
from apps.auth_token.auth import GrafanaIncidentStaticKeyAuth

from .serializers import AlertGroupSerializer


class AlertGroupsView(ReadOnlyModelViewSet):
    authentication_classes = (GrafanaIncidentStaticKeyAuth,)
    queryset = AlertGroup.unarchived_objects.all()
    serializer_class = AlertGroupSerializer
    lookup_field = "public_primary_key"
