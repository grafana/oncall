import pytest
import pytz
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
def test_raise_bad_request_exception_if_not_valid_timezone(input, raises_exception):
    if raises_exception:
        with pytest.raises(BadRequest, match="Invalid timezone"):
            tz.raise_bad_request_exception_if_not_valid_timezone(input)
    else:
        try:
            tz.raise_bad_request_exception_if_not_valid_timezone(input)
        except Exception:
            pytest.fail()


class TestTimeZoneField:
    @pytest.mark.parametrize("tz", pytz.all_timezones)
    def test_valid_timezones(self, tz):
        class MySerializer(serializers.Serializer):
            tz = tz.TimeZoneField()

        try:
            serializer = MySerializer(data={"tz": tz})
            serializer.is_valid(raise_exception=True)

            assert serializer.validated_data["tz"] == tz
        except Exception:
            pytest.fail()

    def test_invalid_timezone(self):
        class MySerializer(serializers.Serializer):
            tz = tz.TimeZoneField()

        with pytest.raises(BadRequest, match="Invalid timezone"):
            serializer = MySerializer(data={"tz": "potato"})
            serializer.is_valid(raise_exception=True)

    def test_it_works_with_allow_null(self):
        class MySerializer(serializers.Serializer):
            tz = tz.TimeZoneField(allow_null=True)

        try:
            serializer = MySerializer(data={"tz": None})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] is None

            serializer = MySerializer(data={"tz": "UTC"})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] == "UTC"
        except Exception:
            pytest.fail()

    def test_it_works_with_required(self):
        class MySerializer(serializers.Serializer):
            tz = tz.TimeZoneField(required=True)

        with pytest.raises(ValidationError, match="This field is required"):
            serializer = MySerializer(data={})
            serializer.is_valid(raise_exception=True)

        try:
            serializer = MySerializer(data={"tz": "UTC"})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] == "UTC"
        except Exception:
            pytest.fail()
