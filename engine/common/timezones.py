import pytz

from common.api_helpers.exceptions import BadRequest


def is_valid_timezone(timezone: str):
    try:
        return pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return False


def raise_exception_if_not_valid_timezone(timezone, exception_class=BadRequest):
    """
    Like `is_valid_timezone` but throws specified "exception_class" class
    (default `common.api_helpers.exceptions.BadRequest`) if not a valid timezone.

    **NOTE**: if `exception_class` is provided, it should take a `detail` kwarg in its constructor
    """
    if not is_valid_timezone(timezone):
        raise exception_class(detail="Invalid timezone")
