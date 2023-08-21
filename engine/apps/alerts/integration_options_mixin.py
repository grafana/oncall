import importlib

from django.conf import settings

from common.utils import getattrd


class IntegrationOptionsMixin:
    DEFAULT_INTEGRATION = "grafana"
    # Import every integration config file listed in settings.INSTALLED_ONCALL_INTEGRATIONS
    # as a submodule into a tuple, e.g. AlertReceiveChannel._config[0].id, slug, description, etc..
    _config = tuple(
        (importlib.import_module(integration_config) for integration_config in settings.INSTALLED_ONCALL_INTEGRATIONS)
    )

    def __init__(self, *args, **kwargs):
        super(IntegrationOptionsMixin, self).__init__(*args, **kwargs)
        # Object integration configs (imported as submodules earlier) are also available in `config` field,
        # e.g. instance.config.id, instance.config.slug, instance.config.description, etc...
        for integration in self._config:
            if integration.slug == self.integration:
                self.config = integration

    # Define variables for backward compatibility, e.g. INTEGRATION_GRAFANA, INTEGRATION_FORMATTED_WEBHOOK, etc...
    for integration_config in _config:
        vars()[f"INTEGRATION_{integration_config.slug.upper()}"] = integration_config.slug

    INTEGRATION_TYPES = {integration_config.slug for integration_config in _config}

    INTEGRATION_CHOICES = tuple(
        (
            (
                integration_config.slug,
                integration_config.title,
            )
            for integration_config in _config
        )
    )

    # Following attributes are generated from _config for backwards compatibility and used across the codebase
    WEB_INTEGRATION_CHOICES = [
        integration_config.slug for integration_config in _config if integration_config.is_displayed_on_web
    ]
    INTEGRATION_SHORT_DESCRIPTION = {
        integration_config.slug: integration_config.short_description for integration_config in _config
    }
    INTEGRATION_FEATURED = [integration_config.slug for integration_config in _config if integration_config.is_featured]
    INTEGRATION_FEATURED_TAG_NAME = {
        integration_config.slug: integration_config.featured_tag_name
        for integration_config in _config
        if hasattr(integration_config, "featured_tag_name")
    }

    # The following attributes dynamically generated and used by apps.alerts.incident_appearance.renderers, templaters
    # e.g. INTEGRATION_TO_DEFAULT_SLACK_TITLE_TEMPLATE, INTEGRATION_TO_DEFAULT_SLACK_MESSAGE_TEMPLATE, etc...
    template_names = [
        "slack_title",
        "slack_message",
        "slack_image_url",
        "web_title",
        "web_message",
        "web_image_url",
        "sms_title",
        "phone_call_title",
        "telegram_title",
        "telegram_message",
        "telegram_image_url",
        "grouping_id",
        "resolve_condition",
        "acknowledge_condition",
        "source_link",
    ]

    for template_name in template_names:
        result = dict()
        for integration_config in _config:
            result[integration_config.slug] = getattrd(integration_config, template_name, None)
        vars()[f"INTEGRATION_TO_DEFAULT_{template_name.upper()}_TEMPLATE"] = result
