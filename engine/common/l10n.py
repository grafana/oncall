import logging
import typing

from babel.core import UnknownLocaleError
from babel.dates import format_datetime, format_time
from django.utils import timezone

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en"


def _format_dt(
    func: typing.Callable[[timezone.datetime, typing.Optional[str]], str],
    dt: timezone.datetime,
    locale: typing.Optional[str],
) -> str:
    format = "short"
    try:
        # can't pass in locale of None otherwise TypeError is raised
        return func(dt, format=format, locale=locale if locale else FALLBACK_LOCALE)
    except UnknownLocaleError:
        logger.warning(
            f"babel.core.UnknownLocaleError encountered, locale={locale}. Will retry with fallback locale of {FALLBACK_LOCALE}"
        )
        return func(dt, format=format, locale=FALLBACK_LOCALE)


def format_localized_datetime(dt: timezone.datetime, locale: typing.Optional[str]) -> str:
    return _format_dt(format_datetime, dt, locale)


def format_localized_time(dt: timezone.datetime, locale: typing.Optional[str]) -> str:
    return _format_dt(format_time, dt, locale)
