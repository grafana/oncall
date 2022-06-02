from django.apps import AppConfig


class TelegramConfig(AppConfig):
    name = "apps.telegram"

    def ready(self):
        import apps.telegram.signals  # noqa: F401
