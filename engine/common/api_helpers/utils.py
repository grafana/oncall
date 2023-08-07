import datetime
import re
import typing
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.validators import URLValidator
from django.utils import dateparse, timezone
from django.utils.regex_helper import _lazy_re_compile
from icalendar import Calendar
from rest_framework import serializers
from rest_framework.request import Request

from apps.schedules.ical_utils import fetch_ical_file
from common.api_helpers.exceptions import BadRequest
from common.timezones import raise_exception_if_not_valid_timezone


class CurrentOrganizationDefault:
    """
    Utility class to get the current organization right from the serializer field.
    In pair with serializers.HiddenField gives an ability to create objects
    without overriding perform_create on the model, while respecting unique_together constraints.
    Example: organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    """

    requires_context = True

    def __call__(self, serializer_field):
        self.organization = serializer_field.context["request"].auth.organization
        return self.organization

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class CurrentTeamDefault:
    """
    Utility class to get the current team right from the serializer field.
    """

    requires_context = True

    def __call__(self, serializer_field):
        self.team = serializer_field.context["request"].user.current_team
        return self.team

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class URLValidatorWithoutTLD(URLValidator):
    """
    Overrides Django URLValidator Regex. It removes the tld part because
    most of the time, containers don't have any TLD in their urls and such outgoing webhooks
    can't be registered.
    """

    host_re = (
        "("
        + URLValidator.hostname_re
        + URLValidator.domain_re
        + URLValidator.tld_re
        + "|"
        + URLValidator.hostname_re
        + "|localhost)"
    )

    regex = _lazy_re_compile(
        r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
        r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
        r"(?:" + URLValidator.ipv4_re + "|" + URLValidator.ipv6_re + "|" + host_re + ")"
        r"(?::[0-9]{1,5})?"  # port
        r"(?:[/?#][^\s]*)?"  # resource path
        r"\Z",
        re.IGNORECASE,
    )


class CurrentUserDefault:
    """
    Utility class to get the current user right from the serializer field.
    """

    requires_context = True

    def __call__(self, serializer_field):
        self.user = serializer_field.context["request"].user
        return self.user

    def __repr__(self):
        return "%s()" % self.__class__.__name__


def validate_ical_url(url):
    if url:
        if settings.BASE_URL in url:
            raise serializers.ValidationError("Potential self-reference")
        try:
            ical_file = fetch_ical_file(url)
            Calendar.from_ical(ical_file)
        except requests.exceptions.RequestException:
            raise serializers.ValidationError("Ical download failed")
        except ValueError:
            raise serializers.ValidationError("Ical parse failed")
        return url
    return None


"""
This utility function is for building a URL when we don't know if the base URL
has been given a trailing / such as reading from environment variable or user
input.  If the base URL is coming from a validated model field urljoin can be used
instead.  Do not use this function to append query parameters since a / is added
to the end of the base URL if there isn't one.
"""


def create_engine_url(path, override_base=None):
    base = settings.BASE_URL
    if override_base:
        base = override_base
    if not base.endswith("/"):
        base += "/"
    trimmed_path = path.lstrip("/")
    return urljoin(base, trimmed_path)


def get_date_range_from_request(request: Request) -> typing.Tuple[str, datetime.date, int]:
    """Extract timezone, starting date and number of days params from request.

    Used mainly for schedules and shifts API.
    """
    user_tz: str = request.query_params.get("user_tz", "UTC")
    raise_exception_if_not_valid_timezone(user_tz)

    date = timezone.now().date()
    date_param = request.query_params.get("date")
    if date_param is not None:
        try:
            date = dateparse.parse_date(date_param)
        except ValueError:
            raise BadRequest(detail="Invalid date format")
        else:
            if date is None:
                raise BadRequest(detail="Invalid date format")

    starting_date = date if request.query_params.get("date") else None
    if starting_date is None:
        # default to current week start
        starting_date = date - datetime.timedelta(days=date.weekday())

    try:
        days = int(request.query_params.get("days", 7))  # fallback to a week
    except ValueError:
        raise BadRequest(detail="Invalid days format")

    return user_tz, starting_date, days


def check_phone_number_is_valid(phone_number):
    return re.match(r"^\+\d{8,15}$", phone_number) is not None


def serialize_datetime_as_utc_timestamp(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
