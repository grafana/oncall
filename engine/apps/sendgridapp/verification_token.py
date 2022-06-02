"""Based on example https://simpleisbetterthancomplex.com/tutorial/2016/08/24/how-to-create-one-time-link.html"""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    # There are the default setting of PASSWORD_RESET_TIMEOUT_DAYS = 3 (days)

    key_salt = "EmailVerificationTokenGenerator" + settings.TOKEN_SALT
    secret = settings.TOKEN_SECRET

    def _make_hash_value(self, user, timestamp):
        team_datetime_timestamp = (
            "" if user.teams.first() is None else user.teams.first().datetime.replace(microsecond=0, tzinfo=None)
        )
        return str(user.pk) + str(timestamp) + str(team_datetime_timestamp) + str(user.email_verified)


email_verification_token_generator = EmailVerificationTokenGenerator()
