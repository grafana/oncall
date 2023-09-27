from importlib import import_module

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.webhooks.models import Webhook


class WebhookPresetOptions:
    WEBHOOK_PRESETS = {}
    for webhook_preset_config in settings.INSTALLED_WEBHOOK_PRESETS:
        module_path, class_name = webhook_preset_config.rsplit(".", 1)
        module = import_module(module_path)
        preset = getattr(module, class_name)()
        WEBHOOK_PRESETS[preset.metadata.id] = preset

    WEBHOOK_PRESET_CHOICES = [webhook_preset.metadata for webhook_preset in WEBHOOK_PRESETS.values()]


@receiver(pre_save, sender=Webhook)
def listen_for_webhook_save(sender: Webhook, instance: Webhook, raw: bool, *args, **kwargs) -> None:
    if instance.preset and not instance.deleted_at:
        if instance.preset in WebhookPresetOptions.WEBHOOK_PRESETS:
            WebhookPresetOptions.WEBHOOK_PRESETS[instance.preset].override_parameters_before_save(instance)
        else:
            raise NotImplementedError(f"Webhook references unknown preset implementation {instance.preset}")


pre_save.connect(listen_for_webhook_save, Webhook)
