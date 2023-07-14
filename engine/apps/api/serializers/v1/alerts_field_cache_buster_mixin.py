import typing

from django.core.cache import cache


class AlertsFieldCacheBusterMixin:
    RENDER_FOR_WEB_FIELD_NAME = "render_for_web"
    RENDER_FOR_CLASSIC_MARKDOWN_FIELD_NAME = "render_for_classic_markdown"
    ALL_FIELD_NAMES = [RENDER_FOR_WEB_FIELD_NAME, RENDER_FOR_CLASSIC_MARKDOWN_FIELD_NAME]

    @classmethod
    def calculate_cache_key(cls, field_name: str, obj: typing.Any) -> str:
        return cls.CACHE_KEY_FORMAT_TEMPLATE.format(field_name=field_name, object_id=obj.id)

    @classmethod
    def bust_object_caches(cls, obj: typing.Any) -> None:
        cache.delete_many([cls.calculate_cache_key(field_name, obj) for field_name in cls.ALL_FIELD_NAMES])
