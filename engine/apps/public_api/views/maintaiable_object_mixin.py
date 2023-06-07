from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.alerts.models import MaintainableObject
from common.api_helpers.exceptions import BadRequest
from common.exceptions import MaintenanceCouldNotBeStartedError


class MaintainableObjectMixin(viewsets.ViewSet):
    """
    Should be inherited by ModelViewSet.
    The target model should be inherited from MaintainableObject.
    """

    @action(detail=True, methods=["post"])
    def maintenance_start(self, request, pk) -> Response:
        instance = self.get_object()

        mode = str(request.data.get("mode", None)).lower()
        duration = request.data.get("duration", None)

        if mode not in [
            str(MaintainableObject.DEBUG_MAINTENANCE_KEY).lower(),
            str(MaintainableObject.MAINTENANCE_KEY).lower(),
        ]:
            raise BadRequest(detail={"mode": ["Unknown mode"]})
        else:
            mode = {str(x[1]).lower(): x[0] for x in MaintainableObject.MAINTENANCE_MODE_CHOICES}[mode]

        try:
            duration = int(duration)  # We intentionally allow agile durations
        except (ValueError, TypeError):
            raise BadRequest(detail={"duration": ["Invalid duration"]})

        try:
            instance.start_maintenance(mode, duration, request.user)
        except MaintenanceCouldNotBeStartedError as e:
            raise BadRequest(detail=str(e))

        return self.retrieve(request, pk)

    @action(detail=True, methods=["post"])
    def maintenance_stop(self, request, pk) -> Response:
        instance = self.get_object()
        user = request.user
        instance.force_disable_maintenance(user)

        return self.retrieve(request, pk)
