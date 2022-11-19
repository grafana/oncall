from django.apps import apps
from django.core.management.base import BaseCommand

from apps.auth_token import crypto


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--override",
            action="store_true",
            help="Allow overriding of existing invites.",
        )

    def handle(self, *args, **options):
        self.stdout.write("-------------------------")
        self.stdout.write("👋 This script will issue an invite token to securely connect the frontend.")
        self.stdout.write(
            f"Maintainers will be happy to help in the slack channel #grafana-oncall: https://slack.grafana.com/"
        )

        DynamicSetting = apps.get_model("base", "DynamicSetting")
        self_hosted_settings = DynamicSetting.objects.get_or_create(
            name="self_hosted_invitations",
            defaults={
                "json_value": {
                    "keys": [],
                }
            },
        )[0]

        if options["override"]:
            self_hosted_settings.json_value["keys"] = []
        else:
            if len(self_hosted_settings.json_value["keys"]) > 0:
                self.stdout.write(
                    f"Whoops, there is already an active invite in the DB. Override it with --override argument."
                )
                return 0

        invite_token = crypto.generate_token_string()
        self_hosted_settings.json_value["keys"].append(invite_token)
        self_hosted_settings.save(update_fields=["json_value"])

        self.stdout.write(f"Your invite token: {self.style.ERROR(invite_token)}, use it in the Grafana OnCall plugin.")
