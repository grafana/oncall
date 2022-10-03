from django.apps import AppConfig


class MattermostConfig(AppConfig):
    name = "apps.mattermost"

    def ready(self):
        from . import signals  # noqa: F401
