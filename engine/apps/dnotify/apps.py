from django.apps import AppConfig


class DNotifyConfig(AppConfig):
    name = "apps.dnotify"

    def ready(self):
        from . import signals  # noqa: F401
