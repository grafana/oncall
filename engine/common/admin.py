from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, Model


class RawForeignKeysMixin:
    model: Model

    @property
    def raw_id_fields(self) -> tuple[str]:
        fields = self.model._meta.fields
        fk_field_names = tuple(str(field.name) for field in fields if isinstance(field, ForeignKey))

        return fk_field_names


class SearchableByIdsMixin:
    model: Model

    @property
    def search_fields(self) -> tuple[str]:
        search_fields = (
            "id",
            "public_primary_key",
        )

        existing_fields = []

        for field in search_fields:
            try:
                self.model._meta.get_field(field)
            except FieldDoesNotExist:
                continue

            existing_fields.append(field)

        return tuple(existing_fields)


class SelectRelatedMixin:
    model: Model
    list_display: tuple[str]

    @property
    def list_select_related(self) -> tuple[str]:
        fk_field_names = []

        for field_name in self.list_display:
            try:
                field = self.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue

            if isinstance(field, ForeignKey):
                fk_field_names.append(str(field.name))

        return tuple(fk_field_names)


class CustomModelAdmin(SearchableByIdsMixin, RawForeignKeysMixin, SelectRelatedMixin, admin.ModelAdmin):
    pass
