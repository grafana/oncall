import pytz
from rest_framework import serializers

from common.api_helpers.exceptions import BadRequest


def is_valid_timezone(timezone: str):
    try:
        return pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return False


def raise_exception_if_not_valid_timezone(timezone, Exception=BadRequest):
    """
    Like `is_valid_timezone` but throws specified Exception class
    (default `common.api_helpers.exceptions.BadRequest`) if not a valid timezone.

    **NOTE**: if an Exception class is provided, it should take a `detail` kwarg in its constructor
    """
    if not is_valid_timezone(timezone):
        raise Exception(detail="Invalid timezone")


class TimeZoneField(serializers.CharField):
    def _validator(self, value: str):
        raise_exception_if_not_valid_timezone(value, serializers.ValidationError)

    def __init__(self, **kwargs):
        super().__init__(validators=[self._validator], **kwargs)
