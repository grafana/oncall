import base64
import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils.dateparse import parse_datetime
from pytz import timezone

from common.jinja_templater import apply_jinja_template, apply_jinja_template_to_alert_payload_and_labels
from common.jinja_templater.apply_jinja_template import (
    JinjaTemplateError,
    JinjaTemplateWarning,
    templated_value_is_truthy,
)

EMAIL_SAMPLE_PAYLOAD = {
    "subject": "[Reminder] Review GKE getServerConfig API permission changes",
    "message": "Hello Google Kubernetes Customer,\r\n"
    "\r\n"
    "We’re writing to remind you that starting October 22, 2024, "
    "the  \r\n"
    "getServerConfig API for Google Kubernetes Engine (GKE) will "
    "enforce  \r\n"
    "Identity and Access Management (IAM) container.clusters.list "
    "checks. This  \r\n"
    "change follows a series of security improvements as IAM  \r\n"
    "container.clusters.list permissions are being enforced across "
    "the  \r\n"
    "getServerConfig API.\r\n"
    "\r\n"
    "We’ve provided additional information below to guide you through "
    "this  \r\n"
    "change.\r\n"
    "\r\n"
    "What you need to know\r\n"
    "\r\n"
    "The current implementation doesn’t apply a specific permissions "
    "check via  \r\n"
    "getServerConfig API. After this change goes into effect for the "
    "Google  \r\n"
    "Kubernetes Engine API getServerConfig, only authorized users with "
    "the  \r\n"
    "container.clusters.list permissions will be able to call the  \r\n"
    "GetServerConfig.\r\n",
    "sender": "someone@somewhere.dev",
}


def test_apply_jinja_template():
    payload = {"name": "test"}
    rendered = apply_jinja_template("{{ payload | tojson_pretty }}", payload)
    result = json.loads(rendered)
    assert payload == result


def test_apply_jinja_template_iso8601_to_time():
    payload = {"name": "2023-11-22T15:30:00.000000000Z"}

    result = apply_jinja_template(
        "{{ payload.name | iso8601_to_time }}",
        payload,
    )
    expected = str(parse_datetime(payload["name"]))
    assert result == expected


def test_apply_jinja_template_timestamp_to_datetime():
    payload = {"sometime": 1730893740}

    result = apply_jinja_template(
        "{{ payload.sometime | timestamp_to_datetime }}",
        payload,
    )
    expected = str(datetime.fromtimestamp(payload["sometime"]))
    assert result == expected


def test_apply_jinja_template_datetimeformat():
    payload = {"aware": "2023-05-28 23:11:12+0000", "naive": "2023-05-28 23:11:12"}

    assert apply_jinja_template(
        "{{ payload.aware | iso8601_to_time | datetimeformat('%Y-%m-%dT%H:%M:%S%z') }}",
        payload,
    ) == parse_datetime(payload["aware"]).strftime("%Y-%m-%dT%H:%M:%S%z")
    assert apply_jinja_template(
        "{{ payload.naive | iso8601_to_time | datetimeformat('%Y-%m-%dT%H:%M:%S%z') }}",
        payload,
    ) == parse_datetime(payload["naive"]).strftime("%Y-%m-%dT%H:%M:%S%z")
    assert apply_jinja_template(
        "{{ payload.aware | datetimeparse('%Y-%m-%d %H:%M:%S%z') | datetimeformat('%Y-%m-%dT%H:%M:%S%z') }}",
        payload,
    ) == datetime.strptime(payload["aware"], "%Y-%m-%d %H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
    assert apply_jinja_template(
        "{{ payload.naive | datetimeparse('%Y-%m-%d %H:%M:%S') | datetimeformat('%Y-%m-%dT%H:%M:%S%z') }}",
        payload,
    ) == datetime.strptime(payload["naive"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S%z")


def test_apply_jinja_template_datetimeformat_as_timezone():
    payload = {"aware": "2023-05-28 23:11:12+0000", "naive": "2023-05-28 23:11:12"}

    assert apply_jinja_template(
        "{{ payload.aware | iso8601_to_time | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'America/Chicago') }}",
        payload,
    ) == parse_datetime(payload["aware"]).astimezone(timezone("America/Chicago")).strftime("%Y-%m-%dT%H:%M:%S%z")
    assert apply_jinja_template(
        "{{ payload.naive | iso8601_to_time | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'America/Chicago') }}",
        payload,
    ) == parse_datetime(payload["naive"]).astimezone(timezone("America/Chicago")).strftime("%Y-%m-%dT%H:%M:%S%z")
    assert (
        apply_jinja_template(
            """{{ payload.aware | datetimeparse('%Y-%m-%d %H:%M:%S%z') | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z',
        'America/Chicago') }}""",
            payload,
        )
        == parse_datetime(payload["aware"]).astimezone(timezone("America/Chicago")).strftime("%Y-%m-%dT%H:%M:%S%z")
    )
    assert (
        apply_jinja_template(
            """{{ payload.naive | datetimeparse('%Y-%m-%d %H:%M:%S') | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z',
        'America/Chicago') }}""",
            payload,
        )
        == parse_datetime(payload["naive"]).astimezone(timezone("America/Chicago")).strftime("%Y-%m-%dT%H:%M:%S%z")
    )

    with pytest.raises(JinjaTemplateWarning):
        apply_jinja_template(
            "{{ payload.aware | iso8601_to_time | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'potato') }}",
            payload,
        )
        apply_jinja_template(
            """{{ payload.aware | datetimeparse('%Y-%m-%d %H:%M:%S%z') |
            datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'potato') }}""",
            payload,
        )


def test_apply_jinja_template_datetimeparse():
    payload = {"aware": "15 05 2024 07:52:11 -0600", "naive": "2024-05-15T07:52:11"}

    assert apply_jinja_template(
        "{{ payload.aware | datetimeparse('%d %m %Y %H:%M:%S %z') }}",
        payload,
    ) == str(datetime.strptime(payload["aware"], "%d %m %Y %H:%M:%S %z"))
    assert apply_jinja_template(
        "{{ payload.naive | datetimeparse('%Y-%m-%dT%H:%M:%S') }}",
        payload,
    ) == str(datetime.strptime(payload["naive"], "%Y-%m-%dT%H:%M:%S"))


def test_apply_jinja_template_timedeltaparse():
    payload = {"seconds": "-100s", "hours": "12h", "days": "-5d", "weeks": "52w"}

    assert apply_jinja_template(
        "{{ payload.seconds | timedeltaparse }}",
        payload,
    ) == str(timedelta(seconds=-100))
    assert apply_jinja_template(
        "{{ payload.hours | timedeltaparse }}",
        payload,
    ) == str(timedelta(hours=12))
    assert apply_jinja_template(
        "{{ payload.days | timedeltaparse }}",
        payload,
    ) == str(timedelta(days=-5))
    assert apply_jinja_template(
        "{{ payload.weeks | timedeltaparse }}",
        payload,
    ) == str(timedelta(weeks=52))


def test_apply_jinja_template_timedelta_arithmetic():
    payload = {
        "dt": "2023-11-22T15:30:00.000000000Z",
        "delta": "1h",
        "before": "2023-11-22T14:30:00.000000000Z",
        "after": "2023-11-22T16:30:00.000000000Z",
    }

    result = apply_jinja_template(
        "{% set delta = payload.delta | timedeltaparse -%}{{ payload.dt | iso8601_to_time - delta }}",
        payload,
    )
    assert result == str(parse_datetime(payload["before"]))
    result = apply_jinja_template(
        "{% set delta = payload.delta | timedeltaparse -%}{{ payload.dt | iso8601_to_time + delta }}",
        payload,
    )
    assert result == str(parse_datetime(payload["after"]))


def test_apply_jinja_template_b64decode():
    payload = {"name": "SGVsbG8sIHdvcmxkIQ=="}

    assert apply_jinja_template(
        "{{ payload.name | b64decode }}",
        payload,
    ) == base64.b64decode(
        payload["name"]
    ).decode("utf-8")


def test_apply_jinja_template_json_dumps():
    payload = {"name": "test"}

    result = apply_jinja_template("{{ payload | json_dumps }}", payload)
    expected = json.dumps(payload)
    assert result == expected


@pytest.mark.filterwarnings("ignore:::jinja2.*")  # ignore regex escape sequence warning
def test_apply_jinja_template_regex_match():
    payload = {
        "name": "test",
        "message": json.dumps(EMAIL_SAMPLE_PAYLOAD),
    }

    assert apply_jinja_template("{{ payload.name | regex_match('.*') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_match('tes') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_match('test1') }}", payload) == "False"
    # check for timeouts
    with patch("common.jinja_templater.filters.REGEX_TIMEOUT", 1):
        assert (
            apply_jinja_template(
                "{{ payload.message | regex_match('(.|\\s)+Severity(.|\\s){2}High(.|\\s)+') }}", payload
            )
            == "False"
        )

    # Check that exception is raised when regex is invalid
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{ payload.name | regex_match('*') }}", payload)


@pytest.mark.filterwarnings("ignore:::jinja2.*")  # ignore regex escape sequence warning
def test_apply_jinja_template_regex_search():
    payload = {
        "name": "test",
        "message": json.dumps(EMAIL_SAMPLE_PAYLOAD),
    }

    assert apply_jinja_template("{{ payload.name | regex_search('.*') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('tes') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('est') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('test1') }}", payload) == "False"
    # check for timeouts
    with patch("common.jinja_templater.filters.REGEX_TIMEOUT", 1):
        assert (
            apply_jinja_template(
                "{{ payload.message | regex_search('(.|\\s)+Severity(.|\\s){2}High(.|\\s)+') }}", payload
            )
            == "False"
        )

    # Check that exception is raised when regex is invalid
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{ payload.name | regex_search('*') }}", payload)


def test_apply_jinja_template_bad_syntax_error():
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{%", payload={})


def test_apply_jinja_template_unknown_filter_error():
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{ payload | to_json_pretty }}", payload={})


def test_apply_jinja_template_unsafe_error():
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{ payload.__init__() }}", payload={})


def test_apply_jinja_template_restricted_error():
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{% for n in range(100) %}Hello{% endfor %}", payload={})


def test_apply_jinja_template_restricted_inside_conditional():
    template = "{% if 'blabla' in payload %}{% for n in range(100) %}Hello{% endfor %}{% endif %}"
    # No exception when condition == False
    apply_jinja_template(template, payload={})
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template(template, payload={"blabla": "test"})


def test_apply_jinja_template_missing_field_warning():
    with pytest.raises(JinjaTemplateWarning):
        apply_jinja_template("{{ payload.field.name }}", payload={})


def test_apply_jinja_template_type_warning():
    with pytest.raises(JinjaTemplateWarning):
        apply_jinja_template("{{ payload.name + 25 }}", payload={"name": "test"})


def test_apply_jinja_template_too_large():
    template = "test" * 20000
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template(template, payload={})


def test_apply_jinja_template_result_truncate():
    payload = {"value": "test" * 20000}
    result = apply_jinja_template("{{ payload.value }}", payload)
    # Length == Limit + 2 to account for '..' appended to end
    assert len(result) == settings.JINJA_RESULT_MAX_LENGTH + 2


@patch("common.jinja_templater.apply_jinja_template.apply_jinja_template")
def test_apply_jinja_template_to_alert_payload_and_labels(mock_apply_jinja_template):
    template = "{{ payload | tojson_pretty }}"
    payload = {"name": "test"}
    labels = {"foo": "bar"}

    result = apply_jinja_template_to_alert_payload_and_labels(template, payload, labels)

    assert result == mock_apply_jinja_template.return_value
    mock_apply_jinja_template.assert_called_once_with(template, payload=payload, labels=labels)


@pytest.mark.parametrize(
    "value,expected",
    [
        (" 1 ", True),
        (" TRUE ", True),
        (" true ", True),
        (" OK ", True),
        (" ok ", True),
        (" 0 ", False),
        (None, False),
        (1, False),
    ],
)
def test_templated_value_is_truthy(value, expected):
    assert templated_value_is_truthy(value) == expected


def test_apply_jinja_template_parse_json():
    payload = {"message": base64.b64encode(b'{"name": "test"}').decode("utf-8")}
    expected_name = "test"

    assert (
        apply_jinja_template(
            "{{ (payload.message | b64decode | parse_json).name }}",
            payload,
        )
        == expected_name
    )
