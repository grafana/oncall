from django.apps import AppConfig


class ZoomConfig(AppConfig):
    name = "apps.zoom"

    def ready(self) -> None:
        import apps.zoom.signals  # noqa: F401
