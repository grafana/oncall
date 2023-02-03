from django.core.management.base import BaseCommand

from apps.twilioapp.twilio_client import twilio_client
from apps.twilioapp.utils import check_phone_number_is_valid
from apps.user_management.models import User


class Command(BaseCommand):
    """
    This command is to manually verify user's phone numbers.
    """

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int, help="User id to manually verify phone number")
        parser.add_argument("phone_number", type=str, help="Phone number to verify")

        parser.add_argument(
            "--override",
            action="store_true",
            help="Override existing phone number",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        phone_number = options["phone_number"]

        if not check_phone_number_is_valid(phone_number):
            self.stdout.write(self.style.ERROR('Invalid phone number "%s"' % phone_number))
            return

        try:
            user = User.objects.get(pk=user_id)
        except User.objects.DoesNotExists:
            self.stdout.write(self.style.ERROR('Invalid user_id "%s"' % user_id))
            return

        if user.verified_phone_number and not options["override"]:
            self.stdout.write(self.style.ERROR('User "%s" already has a phone number' % user_id))
            return

        normalized_phone_number, _ = twilio_client.normalize_phone_number_via_twilio(phone_number)
        if normalized_phone_number:
            user.save_verified_phone_number(normalized_phone_number)
            user.unverified_phone_number = phone_number
            user.save(update_fields=["unverified_phone_number"])
        else:
            self.stdout.write(self.style.ERROR('Invalid phone number "%s"' % phone_number))
            return

        self.stdout.write(
            self.style.SUCCESS('Successfully verified phone number "%s" for user "%s"' % (phone_number, user_id))
        )
