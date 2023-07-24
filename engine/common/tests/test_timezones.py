import pytest
import pytz
from rest_framework.exceptions import APIException

import common.timezones as tz
from common.api_helpers.exceptions import BadRequest


@pytest.mark.parametrize(
    "input,expected",
    [
        ("UTC", pytz.timezone("UTC")),
        ("asdfasdfasdf", False),
    ],
)
def test_is_valid_timezone(input, expected):
    assert tz.is_valid_timezone(input) == expected


@pytest.mark.parametrize(
    "input,raises_exception",
    [
        ("UTC", False),
        ("asdfasdfasdf", True),
    ],
)
def test_raise_exception_if_not_valid_timezone(input, raises_exception):
    if raises_exception:
        with pytest.raises(BadRequest, match="Invalid timezone"):
            tz.raise_exception_if_not_valid_timezone(input)
    else:
        try:
            tz.raise_exception_if_not_valid_timezone(input)
        except Exception:
            pytest.fail()


def test_raise_exception_if_not_valid_timezone_custom_exception():
    class MyCustomException(APIException):
        "asdfasdf"

    with pytest.raises(MyCustomException, match="Invalid timezone"):
        tz.raise_exception_if_not_valid_timezone("asdfasfd", exception_class=MyCustomException)
