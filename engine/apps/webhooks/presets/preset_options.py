from importlib import import_module

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.webhooks.models import Webhook


class WebhookPresetOptions:
    WEBHOOK_PRESETS = {}
    ADVANCED_PRESET_META_DATA = {}
    for webhook_preset_config in settings.INSTALLED_WEBHOOK_PRESETS:
        module_path, class_name = webhook_preset_config.rsplit(".", 1)
        module = import_module(module_path)
        preset = getattr(module, class_name)()
        WEBHOOK_PRESETS[preset.metadata.id] = preset
        if webhook_preset_config == settings.ADVANCED_WEBHOOK_PRESET:
            ADVANCED_PRESET_META_DATA = preset.metadata

    WEBHOOK_PRESET_CHOICES = [webhook_preset.metadata for webhook_preset in WEBHOOK_PRESETS.values()]

    EXAMPLE_PAYLOAD = {
        "event": {"type": "resolve", "time": "2023-04-19T21:59:21.714058+00:00"},
        "user": {"id": "UVMX6YI9VY9PV", "username": "admin", "email": "admin@localhost"},
        "alert_group": {
            "id": "I6HNZGUFG4K11",
            "integration_id": "CZ7URAT4V3QF2",
            "route_id": "RKHXJKVZYYVST",
            "alerts_count": 1,
            "state": "resolved",
            "created_at": "2023-04-19T21:53:48.231148Z",
            "resolved_at": "2023-04-19T21:59:21.714058Z",
            "acknowledged_at": "2023-04-19T21:54:39.029347Z",
            "title": "Incident",
            "permalinks": {
                "slack": None,
                "telegram": None,
                "web": "https://**********.grafana.net/a/grafana-oncall-app/alert-groups/I6HNZGUFG4K11",
            },
        },
        "alert_group_id": "I6HNZGUFG4K11",
        "alert_payload": {
            "endsAt": "0001-01-01T00:00:00Z",
            "labels": {"region": "eu-1", "alertname": "TestAlert"},
            "status": "firing",
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "annotations": {"description": "This alert was sent by user for the demonstration purposes"},
            "generatorURL": "",
        },
        "integration": {
            "id": "CZ7URAT4V3QF2",
            "type": "webhook",
            "name": "Main Integration - Webhook",
            "team": "Webhooks Demo",
        },
        "notified_users": [],
        "users_to_be_notified": [],
        "responses": {
            "WHP936BM1GPVHQ": {
                "id": "7Qw7TbPmzppRnhLvK3AdkQ",
                "created_at": "15:53:50",
                "status": "new",
                "content": {"message": "Ticket created!", "region": "eu"},
            }
        },
    }


@receiver(pre_save, sender=Webhook)
def listen_for_webhook_save(sender: Webhook, instance: Webhook, raw: bool, *args, **kwargs) -> None:
    if instance.preset and not instance.deleted_at:
        if instance.preset in WebhookPresetOptions.WEBHOOK_PRESETS:
            WebhookPresetOptions.WEBHOOK_PRESETS[instance.preset].override_parameters_before_save(instance)
        else:
            raise NotImplementedError(f"Webhook references unknown preset implementation {instance.preset}")


pre_save.connect(listen_for_webhook_save, Webhook)
