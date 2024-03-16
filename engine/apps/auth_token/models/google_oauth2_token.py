from typing import Tuple

from django.db import models
from django.utils import timezone

from apps.auth_token import constants, crypto
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization, User


# def get_expire_date():
#     return timezone.now() + timezone.timedelta(seconds=SLACK_AUTH_TOKEN_TIMEOUT_SECONDS)


# class GoogleAuthTokenQueryset(models.QuerySet):
#     def filter(self, *args, **kwargs):
#         now = timezone.now()
#         return super().filter(*args, **kwargs, revoked_at=None, expire_date__gte=now)

#     def delete(self):
#         self.update(revoked_at=timezone.now())


class GoogleOAuth2Token(models.Model):
    # objects = GoogleAuthTokenQueryset.as_manager()
    user = models.ForeignKey(
        "user_management.User",
        related_name="google_auth_token_set",
        on_delete=models.CASCADE,
    )

    # TODO: what's the best way to store these, should we hash tme?
    # TODO: are these the proper max_length values here?
    # https://developers.google.com/identity/protocols/oauth2#size
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
