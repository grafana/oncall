from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.labels.client import LabelsAPIClient
from apps.labels.models import AlertReceiveChannelAssociatedLabel, Label
from apps.labels.utils import is_labels_enabled
from common.api_helpers.exceptions import BadRequest


class LabelsCRUDView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not is_labels_enabled(self.request.auth.organization):
            raise NotFound

    def get(self, request):  # todo
        organization = self.request.auth.organization
        key_id = self.request.query_params.get("keyID")
        if key_id:
            result = LabelsAPIClient(organization).get_labels_keys()
        else:
            result = LabelsAPIClient(organization).get_label_key_values(key_id)
        return Response(result)

    def post(self, request):  # todo
        organization = self.request.auth.organization
        # {
        #     "key": {"repr": "severity"},
        #     "values": [{"repr": "critical"}]  # []
        # }
        label_data = self.request.data
        result = LabelsAPIClient(organization).create_label(label_data)
        return Response(status=result.status_code)

    def put(self, request):  # todo
        organization = self.request.auth.organization
        key_id = self.request.query_params.get("keyID")
        label_action = self.request.query_params.get("action")
        label_data = self.request.data
        if not key_id or not label_action or not label_data:
            raise BadRequest()
        if label_action == "key_update":
            result = LabelsAPIClient(organization).update_label_key(key_id, label_data)
        elif label_action == "value_update":
            value_id = self.request.query_params.get("valueID")
            if not value_id:
                raise BadRequest()
            result = LabelsAPIClient(organization).update_label_value(key_id, value_id, label_data)
        elif label_action == "value_add":
            # {"repr": "warning"}
            result = LabelsAPIClient(organization).add_value(key_id, label_data)
        else:
            raise BadRequest()
        # result.raise_for_status()
        return Response(status=result.status_code)


class LabelsAssociatingMixin:  # use for labelable objects views (ex. AlertReceiveChannelView)
    def check_if_label_feature_enabled(self):
        """Call this method to block if labels feature is not enabled"""
        if not is_labels_enabled(self.request.auth.organization):
            raise NotFound

    def filter_by_labels(self, queryset):
        """Call this method in `get_queryset()` to add filtering by labels"""
        labels = self.request.query_params.getlist("label")  # ["key1,value1", "key2,value2"]
        if not labels:
            return queryset
        keys = []
        values = []
        for label in labels:
            key_id, value_id = label.split(",")
            keys.append(key_id)
            values.append(value_id)
        return queryset.filter(labels__key_id__in=keys, labels__value_id__in=values)

    @action(methods=["get"], detail=False)
    def labels(self, request):
        self.check_if_label_feature_enabled()
        # associating_labels_class = self.model.associating_labels_class  # todo
        associating_labels_class = AlertReceiveChannelAssociatedLabel
        associated_labels_pk = (
            associating_labels_class.objects.filter(alert_receive_channel__organization=self.request.auth.organization)
            .values_list("label_id", flat=True)
            .distinct()
        )
        labels = Label.objects.filter(pk__in=associated_labels_pk)
        result = [{"key_id": label.key_id, "value_id": label.value_id} for label in labels]
        return Response(result)

    @action(methods=["post"], detail=True)
    def associate_label(self, request, pk):
        self.check_if_label_feature_enabled()
        organization = self.request.auth.organization
        key_id = request.data.get("key_id")
        value_id = request.data.get("value_id")
        obj = self.get_object()
        Label.associate(key_id, value_id, obj, organization)
        return Response(status=200)

    @action(methods=["post"], detail=True)
    def remove_label(self, request, pk):
        self.check_if_label_feature_enabled()
        organization = self.request.auth.organization
        key_id = request.data.get("key_id")
        value_id = request.data.get("value_id")
        obj = self.get_object()
        Label.remove(key_id, value_id, obj, organization)
        return Response(status=200)
