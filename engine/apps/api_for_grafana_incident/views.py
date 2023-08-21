from rest_framework import mixins, viewsets

from apps.alerts.models import AlertGroup
from apps.auth_token.auth import GrafanaIncidentStaticKeyAuth

from .serializers import AlertGroupSerializer


class RetrieveViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides only `retrieve` actions.
    """


class AlertGroupsView(RetrieveViewSet):
    authentication_classes = (GrafanaIncidentStaticKeyAuth,)
    queryset = AlertGroup.objects.all()
    serializer_class = AlertGroupSerializer
    lookup_field = "public_primary_key"
