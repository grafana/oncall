from django.utils import timezone

from common import l10n

REAL_LOCALE = "fr_CA"
FAKE_LOCALE = "potato"
dt = timezone.datetime(2022, 5, 4, 15, 14, 13, 12)


def test_format_localized_datetime():
    assert l10n.format_localized_datetime(dt, REAL_LOCALE) == "2022-05-04 15 h 14"

    # test that it catches the exception and falls back to some configured default
    assert l10n.format_localized_datetime(dt, FAKE_LOCALE) == "5/4/22, 3:14\u202fPM"

    # test that it properly handles None and falls back to some configured default
    assert l10n.format_localized_datetime(dt, None) == "5/4/22, 3:14\u202fPM"


def test_format_localized_time():
    assert l10n.format_localized_time(dt, REAL_LOCALE) == "15 h 14"

    # test that it catches the exception and falls back to some configured default
    assert l10n.format_localized_time(dt, FAKE_LOCALE) == "3:14\u202fPM"

    # test that it properly handles None and falls back to some configured default
    assert l10n.format_localized_time(dt, None) == "3:14\u202fPM"
