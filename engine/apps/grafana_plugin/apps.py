import logging
import sys

from django.apps import AppConfig
from django.conf import settings
from django.db import OperationalError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STARTUP_COMMANDS = ["runserver", "uwsgi"]


class GrafanaPluginConfig(AppConfig):
    name = "apps.grafana_plugin"

    def ready(self):
        """
        For OSS installations, validate that GRAFANA_API_URL environment variable is specified, otherwise
        abort app startup.

        We only care to run this for OSS INSTALLATIONS. The STARTUP_COMMANDS check is to avoid running this check
        for the django migrate command. For a fresh installation this would crash because user_management table would
        [not exist](https://stackoverflow.com/a/63326719).
        """
        # TODO: this logic should probably be moved out to a common utility
        is_not_migration_script = any(startup_command in sys.argv for startup_command in STARTUP_COMMANDS)
        if is_not_migration_script and settings.IS_OPEN_SOURCE:
            try:
                from apps.user_management.models import Organization

                has_existing_org = Organization.objects.first() is not None

                # only enforce the following for new setups - if no organization exists in the database
                # and the GRAFANA_API_URL env var is not specified, exit the application
                if has_existing_org is False and settings.SELF_HOSTED_SETTINGS["GRAFANA_API_URL"] is None:
                    logger.error(
                        "For OSS installations, GRAFANA_API_URL is a required environment variable. Please set it and restart the application."
                    )
                    sys.exit()
            except OperationalError:
                pass
