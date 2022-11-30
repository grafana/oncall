import pytz
from rest_framework import serializers

from common.api_helpers.exceptions import BadRequest


def is_valid_timezone(timezone: str):
    try:
        return pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return False


def raise_bad_request_exception_if_not_valid_timezone(timezone):
    """
    Like `is_valid_timezone` from `common.utils` but throws a `BadRequest`
    exception if not a valid timezone
    """
    if not is_valid_timezone(timezone):
        raise BadRequest(detail="Invalid timezone")


class TimeZoneField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(validators=[raise_bad_request_exception_if_not_valid_timezone], **kwargs)
