import importlib

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.webhooks.models import Webhook


class WebhookPresetOptions:
    _config = tuple(
        (importlib.import_module(webhook_preset_config) for webhook_preset_config in settings.INSTALLED_WEBHOOK_PRESETS)
    )

    WEBHOOK_PRESET_CHOICES = [webhook_preset.metadata for webhook_preset in _config]
    WEBHOOK_PRESET_OVERRIDE = {
        webhook_preset.metadata["id"]: webhook_preset.override_webhook_parameters for webhook_preset in _config
    }


@receiver(pre_save, sender=Webhook)
def listen_for_webhook_save(sender: Webhook, instance: Webhook, raw: bool, *args, **kwargs) -> None:
    if instance.preset:
        if instance.preset in WebhookPresetOptions.WEBHOOK_PRESET_OVERRIDE:
            WebhookPresetOptions.WEBHOOK_PRESET_OVERRIDE[instance.preset](instance)
        else:
            raise NotImplementedError(f"Webhook references unknown preset implementation {instance.preset}")


pre_save.connect(listen_for_webhook_save, Webhook)
