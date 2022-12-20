from django.core.management.base import BaseCommand, CommandError

from apps.base.models.dynamic_setting import DynamicSetting
from apps.user_management.models.organization import Organization


class Command(BaseCommand):
    note = "Note: you will also need to set the appropriate environment variables in your ./dev/.env.dev file."
    help = f"Handles the database portion of enabling the mobile app related features. {note}"

    def handle(self, *args, **options):
        org = Organization.objects.first()

        if not org:
            raise CommandError("No organization exists. Have you enabled, and configured, the plugin?")

        DynamicSetting.objects.update_or_create(
            name="mobile_app_settings", defaults={"json_value": {"org_ids": [org.pk]}}
        )

        self.stdout.write(self.style.SUCCESS(f"Mobile app successfully enabled."))
