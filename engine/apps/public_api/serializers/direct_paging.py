from apps.api.serializers.direct_paging import BasePagingSerializer


class DirectPagingSerializer(BasePagingSerializer):
    """
    Very similar to `apps.api.serializers.direct_paging.DirectPagingSerializer` except that
    there is no `grafana_incident_id` attribute
    """
