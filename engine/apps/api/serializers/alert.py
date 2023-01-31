from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertWebRenderer
from apps.alerts.models import Alert


class AlertFieldsCacheSerializerMixin:
    @classmethod
    def get_or_set_cached_web_template_field(
        cls,
        obj,
        field_name,
        renderer_class,
        cache_lifetime=60 * 60 * 24,
    ):
        CACHE_KEY = f"{field_name}_alert_{obj.id}"
        cached_field = cache.get(CACHE_KEY, None)

        web_templates_modified_at = obj.channel.web_templates_modified_at

        if cached_field is not None and (
            web_templates_modified_at is None or cached_field.get("cache_created_at") > web_templates_modified_at
        ):
            field = cached_field.get(field_name)
        else:
            field = renderer_class(obj, obj.last_alert).render()
            cache.set(CACHE_KEY, {"cache_created_at": timezone.now(), field_name: field}, cache_lifetime)

        return field


class AlertSerializer(AlertFieldsCacheSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    render_for_web = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id",
            "link_to_upstream_details",
            "render_for_web",
            "created_at",
        ]

    def get_render_for_web(self, obj):
        if not obj.last_alert:
            return {}
        return AlertFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            "render_for_web",
            AlertWebRenderer,
        )


class AlertRawSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Alert
        fields = [
            "id",
            "raw_request_data",
        ]
