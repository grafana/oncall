from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    name = "apps.webhooks"

    def ready(self) -> None:
        from . import signals  # noqa: F401
