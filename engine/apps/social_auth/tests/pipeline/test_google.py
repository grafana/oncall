import pytest

from apps.social_auth.pipeline import google


SCOPES_ALWAYS_GRANTED = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


@pytest.mark.parametrize(
    "granted_scopes,expected",
    (
        (SCOPES_ALWAYS_GRANTED, False),
        (SCOPES_ALWAYS_GRANTED + ["https://www.googleapis.com/auth/calendar.events.readonly"], True),
    ),
)
def test_user_granted_all_required_scopes(granted_scopes, expected):
    assert google.user_granted_all_required_scopes(granted_scopes) == expected
