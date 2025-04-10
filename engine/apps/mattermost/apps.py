from django.apps import AppConfig


class MattermostConfig(AppConfig):
    name = "apps.mattermost"

    def ready(self) -> None:
        import apps.mattermost.signals  # noqa: F401
