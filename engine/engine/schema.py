from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import get_view_model

from common.api_helpers.mixins import PublicPrimaryKeyMixin


class CustomAutoSchema(AutoSchema):
    def _get_serializer(self):
        """Makes so that extra actions (@action on viewset) don't inherit the serializer from the viewset."""
        if self._is_extra_action:
            return None
        return super()._get_serializer()

    def _get_paginator(self):
        """Makes so that extra actions (@action on viewset) don't inherit the paginator from the viewset."""
        if self._is_extra_action:
            return None
        return super()._get_paginator()

    def get_filter_backends(self):
        """Makes so that extra actions (@action on viewset) don't inherit the filter backends from the viewset."""
        if self._is_extra_action:
            return []
        return super().get_filter_backends()

    def _resolve_path_parameters(self, variables):
        """A workaround to make public primary keys appear as strings in the OpenAPI schema."""

        parameters = super()._resolve_path_parameters(variables)
        if not isinstance(self.view, PublicPrimaryKeyMixin):
            return parameters

        for parameter in parameters:
            if parameter["name"] == "id" and parameter["in"] == "path":
                parameter["schema"]["type"] = "string"
                model = get_view_model(self.view, emit_warnings=False)
                model_name = model._meta.verbose_name if model else "resource"
                parameter["description"] = f"A string identifying this {model_name}."

        return parameters

    @property
    def _is_extra_action(self) -> bool:
        try:
            return self.view.action in [action.__name__ for action in self.view.get_extra_actions()]
        except AttributeError:
            return False
