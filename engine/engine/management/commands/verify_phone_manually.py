from django.apps import apps
from django.core.management.base import BaseCommand

from apps.twilioapp.twilio_client import twilio_client


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--user_ids", type=int, nargs="+", help="User ids to manually verify their unverified_phone_number."
        )
        parser.add_argument(
            "--override",
            action="store_true",
            help="Allow overriding of existing invites.",
        )

    def handle(self, *args, **options):
        user_ids = options["user_ids"]

        User = apps.get_model("user_management", "User")
        users = User.objects.filter(pk__in=user_ids)
        for u in users:
            if u.unverified_phone_number is None:
                self.stdout.write(f"verify_phone_manually: user {u.id} unverified_phone_number is None")
                continue
            if u.verified_phone_number is not None:
                self.stdout.write(f"verify_phone_manually: user {u.id} has already verified_phone_number")
                continue
            normalized_phone_number, _ = twilio_client.normalize_phone_number_via_twilio(u.unverified_phone_number)
            if normalized_phone_number:
                u.save_verified_phone_number(normalized_phone_number)
            else:
                self.stdout.write(f"verify_phone_manually: user {u.id} invalid unverified_phone_number")
                continue
            self.stdout.write(f"verify_phone_manually: user {u.id} success")
