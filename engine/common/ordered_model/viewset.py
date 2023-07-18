from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from common.api_helpers.exceptions import BadRequest
from common.insight_log import EntityEvent, write_resource_insight_log


class OrderedModelViewSet(ModelViewSet):
    """Ordered model viewset to be used in internal API."""

    @action(detail=True, methods=["put"])
    def move_to_position(self, request: Request, pk: int) -> Response:
        instance = self.get_object()
        position = self._get_move_to_position_param(request)

        prev_state = self._get_insight_logs_serialized(instance)
        try:
            instance.to_index(position)
        except IndexError:
            raise BadRequest(detail="Invalid position")
        new_state = self._get_insight_logs_serialized(instance)

        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def _get_insight_logs_serialized(instance):
        try:
            return instance.insight_logs_serialized
        except AttributeError:
            return instance.user.insight_logs_serialized  # workaround for UserNotificationPolicy

    @staticmethod
    def _get_move_to_position_param(request: Request) -> int:
        """
        Get "position" parameter from query params + validate it.
        Used by actions on ordered models (e.g. move_to_position).
        """

        class MoveToPositionQueryParamsSerializer(serializers.Serializer):
            position = serializers.IntegerField()

        serializer = MoveToPositionQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data["position"]
