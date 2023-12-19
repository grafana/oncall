import datetime
from zoneinfo import ZoneInfo

import pytest
import pytz
from rest_framework import serializers

import common.api_helpers.custom_fields as cf


class TestTimeZoneField:
    @pytest.mark.parametrize("tz", pytz.all_timezones)
    def test_valid_timezones(self, tz):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField()

        try:
            serializer = MySerializer(data={"tz": tz})
            serializer.is_valid(raise_exception=True)

            assert serializer.validated_data["tz"] == tz
        except Exception:
            pytest.fail()

    def test_invalid_timezone(self):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField()

        with pytest.raises(serializers.ValidationError, match="Invalid timezone"):
            serializer = MySerializer(data={"tz": "potato"})
            serializer.is_valid(raise_exception=True)

    def test_it_works_with_allow_null(self):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField(allow_null=True)

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
            tz = cf.TimeZoneField(required=True)

        with pytest.raises(serializers.ValidationError, match="This field is required"):
            serializer = MySerializer(data={})
            serializer.is_valid(raise_exception=True)

        try:
            serializer = MySerializer(data={"tz": "UTC"})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] == "UTC"
        except Exception:
            pytest.fail()


class TestTimeZoneAwareDatetimeField:
    @pytest.mark.parametrize(
        "test_case,expected_persisted_value",
        [
            # UTC format
            ("2023-07-20T12:00:00Z", datetime.datetime(2023, 7, 20, 12, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC format w/ microseconds
            ("2023-07-20T12:00:00.245652Z", datetime.datetime(2023, 7, 20, 12, 0, 0, 245652, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ colons + no microseconds
            ("2023-07-20T12:00:00+07:00", datetime.datetime(2023, 7, 20, 5, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ colons + microseconds
            (
                "2023-07-20T12:00:00.245652+07:00",
                datetime.datetime(2023, 7, 20, 5, 0, 0, 245652, tzinfo=ZoneInfo("UTC")),
            ),
            # UTC offset w/ no colons + no microseconds
            ("2023-07-20T12:00:00+0700", datetime.datetime(2023, 7, 20, 5, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ no colons + microseconds
            (
                "2023-07-20T12:00:00.245652+0700",
                datetime.datetime(2023, 7, 20, 5, 0, 0, 245652, tzinfo=ZoneInfo("UTC")),
            ),
            ("2023-07-20 12:00:00", None),
            ("20230720T120000Z", None),
        ],
    )
    def test_various_datetimes(self, test_case, expected_persisted_value):
        class MySerializer(serializers.Serializer):
            dt = cf.TimeZoneAwareDatetimeField()

        serializer = MySerializer(data={"dt": test_case})

        if expected_persisted_value:
            serializer.is_valid(raise_exception=True)

            assert serializer.validated_data["dt"] == expected_persisted_value
        else:
            with pytest.raises(serializers.ValidationError):
                serializer.is_valid(raise_exception=True)
