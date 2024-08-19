import pytest

from apps.google import utils

SCOPES_ALWAYS_GRANTED = (
    "openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
)


@pytest.mark.parametrize(
    "granted_scopes,expected",
    (
        (SCOPES_ALWAYS_GRANTED, False),
        (f"{SCOPES_ALWAYS_GRANTED} https://www.googleapis.com/auth/calendar.events.readonly", True),
    ),
)
def test_user_granted_all_required_scopes(granted_scopes, expected):
    assert utils.user_granted_all_required_scopes(granted_scopes) == expected
