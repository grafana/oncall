import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.alerts.models import AlertReceiveChannel
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


class LabelsViewSet(ViewSet):
    """
    Proxy requests to labels-app to create/update labels
    """

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)
    # todo: permissions on create/update labels

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not is_labels_feature_enabled(self.request.auth.organization):
            raise NotFound

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


class LabelsAssociatingMixin:  # use for labelable objects views (ex. AlertReceiveChannelView)
    def filter_by_labels(self, queryset):
        """Call this method in `get_queryset()` to add filtering by labels"""
        if not is_labels_feature_enabled(self.request.auth.organization):
            return queryset
        labels = self.request.query_params.getlist("label")  # ["key1:value1", "key2:value2"]
        if not labels:
            return queryset
        for label in labels:
            label_data = label.split(":")
            if len(label_data) != 2:  # ["key1", "value1"]
                continue
            key_id, value_id = label_data
            queryset &= AlertReceiveChannel.objects_with_deleted.filter(
                labels__key_id=key_id, labels__value_id=value_id
            ).distinct()
        return queryset

    def paginate_queryset(self, queryset):
        organization = self.request.auth.organization
        data = super().paginate_queryset(queryset)
        if not is_labels_feature_enabled(self.request.auth.organization):
            return data
        ids = [d.id for d in data]
        logger.info(f"start update_instances_labels_cache for ids: {ids}")
        update_instances_labels_cache.apply_async((organization.id, ids, self.model.__name__))
        return data
