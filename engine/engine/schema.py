from drf_spectacular.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    def _get_serializer(self):
        """Makes so that extra actions (@action on viewset) don't inherit serializer from the viewset."""
        if self._is_extra_action:
            return None
        return super()._get_serializer()

    def _get_paginator(self):
        if self._is_extra_action:
            return None
        return super()._get_paginator()

    def _get_filter_parameters(self):
        if self._is_extra_action:
            return []
        return super()._get_filter_parameters()

    @property
    def _is_extra_action(self) -> bool:
        try:
            return self.view.action in [action.__name__ for action in self.view.get_extra_actions()]
        except AttributeError:
            return False
