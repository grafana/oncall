from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.api.serializers.labels import LabelDataSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.labels.client import LabelsAPIClient
from apps.labels.models import Label
from apps.labels.utils import is_labels_enabled
from common.api_helpers.exceptions import BadRequest


class LabelsCRUDView(ViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)
    # todo: permissions on create/update labels

    # def initial(self, request, *args, **kwargs):
    #     super().initial(request, *args, **kwargs)
    #     if not is_labels_enabled(self.request.auth.organization):
    #         raise NotFound

    def get_keys(self, request):  # todo
        organization = self.request.auth.organization
        result, _ = LabelsAPIClient(organization.grafana_url, organization.api_token).get_keys()
        return Response(result)

    def get_key(self, request, key_id):  # todo
        organization = self.request.auth.organization
        result, _ = LabelsAPIClient(organization.grafana_url, organization.api_token).get_values(key_id)
        # todo: update cache
        return Response(result)

    def create_label(self, request):
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest()
        result, _ = LabelsAPIClient(organization.grafana_url, organization.api_token).create_label(label_data)
        return Response()

    def add_value(self, request, key_id):
        organization = self.request.auth.organization
        label_data = self.request.data
        if not label_data:
            raise BadRequest()
        result, _ = LabelsAPIClient(organization.grafana_url, organization.api_token).add_value(key_id, label_data)
        return Response()


class LabelsAssociatingMixin:  # use for labelable objects views (ex. AlertReceiveChannelView)
    def check_if_label_feature_enabled(self):
        """Call this method to block if labels feature is not enabled"""
        if not is_labels_enabled(self.request.auth.organization):
            raise NotFound

    def filter_by_labels(self, queryset):
        """Call this method in `get_queryset()` to add filtering by labels"""
        labels = self.request.query_params.getlist("label")  # ["key1:value1", "key2:value2"]
        if not labels:
            return queryset
        for label in labels:
            key_id, value_id = label.split(":")
            queryset &= queryset.filter(labels__key_id=key_id, labels__value_id=value_id)
        return queryset

    @action(methods=["get"], detail=True)
    def labels(self, request, pk):  # todo
        self.check_if_label_feature_enabled()
        obj = self.get_object()
        labels = obj.labels.all().select_related("key_cache", "value_cache")
        result = [
            {
                "key": {"id": label.key_id, "repr": label.key_cache.key_repr},
                "value": {"id": label.value_id, "repr": label.value_cache.value_repr},
            }
            for label in labels
        ]
        return Response(result)

    @action(methods=["post"], detail=True)
    def associate_label(self, request, pk):
        self.check_if_label_feature_enabled()
        organization = self.request.auth.organization
        # {"key": {"id": key_id, "repr": "severity"}, "value": {"id": value_id, "repr": "critical"}}
        serializer = LabelDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = self.get_object()
        Label.associate(request.data, obj, organization)
        return Response(status=200)

    @action(methods=["post"], detail=True)
    def remove_label(self, request, pk):
        self.check_if_label_feature_enabled()
        # organization = self.request.auth.organization
        # {"key": {"id": key_id, "repr": "severity"}, "value": {"id": value_id, "repr": "critical"}}
        serializer = LabelDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = self.get_object()
        Label.remove(request.data, obj)
        return Response(status=200)
