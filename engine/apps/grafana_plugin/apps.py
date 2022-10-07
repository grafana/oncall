import logging
import sys

from django.apps import AppConfig, apps
from django.conf import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GrafanaPluginConfig(AppConfig):
    name = "apps.grafana_plugin"

    def ready(self):
        """
        For OSS installations, validate that GRAFANA_API_URL environment variable is specified, otherwise
        abort app startup.

        We only care to run this for OSS_INSTALLATIONS. The `"runserver" in sys.argv` check is to avoid running this
        for the django migrate command. For a fresh installation this would crash because user_management table would
        [not exist](https://stackoverflow.com/a/63326719).
        """
        if "runserver" in sys.argv and settings.OSS_INSTALLATION is True:
            Organization = apps.get_model("user_management", "Organization")
            has_existing_org = Organization.objects.first() is not None

            # only enforce the following for new setups - if no organization exists in the database
            # and the GRAFANA_API_URL env var is not specified, exit the application
            if has_existing_org is False and settings.SELF_HOSTED_SETTINGS["GRAFANA_API_URL"] is None:
                logger.error(
                    f"For OSS installations, GRAFANA_API_URL is a required environment variable. Please set it and restart the application."
                )
                sys.exit()
