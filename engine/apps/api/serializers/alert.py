from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertWebRenderer
from apps.alerts.models import Alert

from .alerts_field_cache_buster_mixin import AlertsFieldCacheBusterMixin


class AlertFieldsCacheSerializerMixin(AlertsFieldCacheBusterMixin):
    CACHE_KEY_FORMAT_TEMPLATE = "{field_name}_alert_{object_id}"

    @classmethod
    def get_or_set_web_template_field(
        cls,
        obj,
        field_name,
        renderer_class,
        cache_lifetime=60 * 60 * 24,
    ):
        CACHE_KEY = cls.calculate_cache_key(field_name, obj)
        cached_field = cache.get(CACHE_KEY, None)

        web_templates_modified_at = obj.group.channel.web_templates_modified_at

        # use cache only if cache exists
        # and either web templates never modified
        # or cache was created after templates were modified
        if cached_field is not None and (
            web_templates_modified_at is None or cached_field.get("cache_created_at") > web_templates_modified_at
        ):
            field = cached_field.get(field_name)
        else:
            field = renderer_class(obj).render()
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
        return AlertFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            AlertFieldsCacheSerializerMixin.RENDER_FOR_WEB_FIELD_NAME,
            AlertWebRenderer,
        )


class AlertRawSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    raw_request_data = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id",
            "raw_request_data",
        ]

    def get_raw_request_data(self, obj):
        # TODO:
        return {} if obj.group.is_restricted else obj.raw_request_data
