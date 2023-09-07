import importlib

from django.conf import settings


class WebhookPresetOptions:
    _config = tuple(
        (importlib.import_module(webhook_preset_config) for webhook_preset_config in settings.INSTALLED_WEBHOOK_PRESETS)
    )

    WEBHOOK_PRESET_CHOICES = tuple(
        (
            (
                webhook_preset.id,
                webhook_preset.title,
            )
            for webhook_preset in _config
        )
    )

    WEBHOOK_PRESET_FACTORIES = {webhook_preset.id: webhook_preset.create_webhook for webhook_preset in _config}
    WEBHOOK_PRESET_VALIDATORS = {webhook_preset.id: webhook_preset.validate for webhook_preset in _config}
    WEBHOOK_PRESET_POST_PROCESSORS = {webhook_preset.id: webhook_preset.post_process for webhook_preset in _config}
