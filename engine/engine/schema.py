import typing

from drf_spectacular.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    def get_request_serializer(self) -> typing.Any:
        """Makes so that extra actions (@action on viewset) don't inherit request serializer from the viewset."""
        if self._is_extra_action:
            return None
        return super().get_request_serializer()

    def get_response_serializers(self) -> typing.Any:
        """Makes so that extra actions (@action on viewset) don't inherit response serializer from the viewset."""
        if self._is_extra_action:
            return None
        return super().get_response_serializers()

    @property
    def _is_extra_action(self) -> bool:
        return self.view.action in [action.__name__ for action in self.view.get_extra_actions()]
