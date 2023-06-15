from rest_framework import serializers
from rest_framework.request import Request


def get_move_to_position_param(request: Request):
    """
    Get "position" parameter from query params + validate it.
    Used by actions on ordered models (e.g. move_to_position).
    """

    class MoveToPositionQueryParamsSerializer(serializers.Serializer):
        position = serializers.IntegerField()

    serializer = MoveToPositionQueryParamsSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data["position"]
