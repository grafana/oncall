from django.db.models import CharField
from django.db.models.functions import Cast
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.alerts.models import Alert
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers.alerts import AlertSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.mixins import DemoTokenMixin, RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class AlertView(RateLimitHeadersMixin, DemoTokenMixin, mixins.ListModelMixin, GenericViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = Alert
    serializer_class = AlertSerializer
    pagination_class = FiftyPageSizePaginator

    demo_default_id = public_api_constants.DEMO_ALERT_IDS[0]

    def get_queryset(self):
        alert_group_id = self.request.query_params.get("alert_group_id", None)
        search = self.request.query_params.get("search", None)

        queryset = Alert.objects.filter(group__channel__organization=self.request.auth.organization)

        if alert_group_id:
            queryset = queryset.filter(group__public_primary_key=alert_group_id)

        if search:
            queryset = queryset.annotate(
                raw_request_data_str=Cast("raw_request_data", output_field=CharField())
            ).filter(raw_request_data_str__icontains=search)

        queryset = self.serializer_class.setup_eager_loading(queryset)

        return queryset
