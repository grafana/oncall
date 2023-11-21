import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.api.permissions import BasicRolePermission, LegacyAccessControlRole
from apps.api.serializers.labels import (
    LabelKeySerializer,
    LabelKeyValuesSerializer,
    LabelReprSerializer,
    LabelValueSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.labels.client import LabelsAPIClient
from apps.labels.tasks import update_instances_labels_cache, update_labels_cache
from apps.labels.utils import is_labels_feature_enabled
from common.api_helpers.exceptions import BadRequest

logger = logging.getLogger(__name__)


class LabelsFeatureFlagViewSet(ViewSet):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not is_labels_feature_enabled(self.request.auth.organization):
            raise NotFound


class LabelsViewSet(LabelsFeatureFlagViewSet):
    """
    Proxy requests to labels-app to create/update labels
    """

    permission_classes = (IsAuthenticated, BasicRolePermission)
    authentication_classes = (PluginAuthentication,)
    basic_role_permissions = {
        "get_keys": LegacyAccessControlRole.VIEWER,
        "get_key": LegacyAccessControlRole.VIEWER,
        "get_value": LegacyAccessControlRole.VIEWER,
        "rename_key": LegacyAccessControlRole.EDITOR,
        "create_label": LegacyAccessControlRole.EDITOR,
        "add_value": LegacyAccessControlRole.EDITOR,
        "rename_value": LegacyAccessControlRole.EDITOR,
    }

    @extend_schema(responses=LabelKeySerializer(many=True))
    def get_keys(self, request):
        """List of labels keys"""
        organization = self.request.auth.organization
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).get_keys()
        return Response(result, status=response_info["status_code"])

    @extend_schema(responses=LabelKeyValuesSerializer)
    def get_key(self, request, key_id):
        """Key with the list of values"""
        organization = self.request.auth.organization
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).get_values(key_id)
        self._update_labels_cache(result)
        return Response(result, status=response_info["status_code"])

    @extend_schema(responses=LabelValueSerializer)
    def get_value(self, request, key_id, value_id):
        """Value name"""
        organization = self.request.auth.organization
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).get_value(
            key_id, value_id
        )
        self._update_labels_cache(result)
        return Response(result, status=response_info["status_code"])

    @extend_schema(request=LabelReprSerializer, responses=LabelKeyValuesSerializer)
    def rename_key(self, request, key_id):
        """Rename the key"""
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest(detail="name is required")
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).rename_key(
            key_id, label_data
        )
        self._update_labels_cache(result)
        return Response(result, status=response_info["status_code"])

    @extend_schema(
        request=inline_serializer(
            name="LabelCreateSerializer",
            fields={"key": LabelReprSerializer(), "values": LabelReprSerializer(many=True)},
            many=True,
        ),
        responses={201: LabelKeyValuesSerializer},
    )
    def create_label(self, request):
        """Create a new label key with values(Optional)"""
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest(detail="key data (name, values) is required")
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).create_label(
            label_data
        )
        return Response(result, status=response_info["status_code"])

    @extend_schema(request=LabelReprSerializer, responses=LabelKeyValuesSerializer)
    def add_value(self, request, key_id):
        """Add a new value to the key"""
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest(detail="name is required")
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).add_value(
            key_id, label_data
        )
        return Response(result, status=response_info["status_code"])

    @extend_schema(request=LabelReprSerializer, responses=LabelKeyValuesSerializer)
    def rename_value(self, request, key_id, value_id):
        """Rename the value"""
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest(detail="name is required")
        result, response_info = LabelsAPIClient(organization.grafana_url, organization.api_token).rename_value(
            key_id, value_id, label_data
        )
        self._update_labels_cache(result)
        return Response(result, status=response_info["status_code"])

    def _update_labels_cache(self, label_data):
        if not label_data:
            return
        serializer = LabelKeyValuesSerializer(data=label_data)
        if serializer.is_valid():
            update_labels_cache.apply_async((label_data,))


class AlertGroupLabelsViewSet(LabelsFeatureFlagViewSet):
    """
    This viewset is similar to LabelsViewSet, but it works with alert group labels.
    Alert group labels are stored in the database, not in the label repo.
    """

    permission_classes = (IsAuthenticated, BasicRolePermission)
    authentication_classes = (PluginAuthentication,)
    basic_role_permissions = {
        "get_keys": LegacyAccessControlRole.VIEWER,
        "get_key": LegacyAccessControlRole.VIEWER,
    }

    @extend_schema(responses=LabelKeySerializer(many=True))
    def get_keys(self, request):
        """
        List of alert group label keys.
        IDs are the same as names to keep the response format consistent with LabelsViewSet.get_keys().
        """
        names = self.request.auth.organization.alert_group_labels.values_list("key_name", flat=True).distinct()
        return Response([{"id": name, "name": name} for name in names])

    @extend_schema(responses=LabelKeyValuesSerializer)
    def get_key(self, request, key_id):
        """Key with the list of values. IDs and names are interchangeable (see get_keys() for more details)."""
        values = (
            self.request.auth.organization.alert_group_labels.filter(key_name=key_id)
            .values_list("value_name", flat=True)
            .distinct()
        )
        return Response(
            {"key": {"id": key_id, "name": key_id}, "values": [{"id": value, "name": value} for value in values]}
        )


def schedule_update_label_cache(model_name, org, ids):
    if not is_labels_feature_enabled(org):
        return
    logger.info(f"start update_instances_labels_cache for ids: {ids}")
    update_instances_labels_cache.apply_async((org.id, ids, model_name))
