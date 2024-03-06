import base64
import json
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

    with pytest.raises(JinjaTemplateWarning):
        apply_jinja_template(
            "{{ payload.aware | iso8601_to_time | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'potato') }}",
            payload,
        )


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


def test_apply_jinja_template_regex_match():
    payload = {"name": "test"}

    assert apply_jinja_template("{{ payload.name | regex_match('.*') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_match('tes') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_match('test1') }}", payload) == "False"

    # Check that exception is raised when regex is invalid
    with pytest.raises(JinjaTemplateError):
        apply_jinja_template("{{ payload.name | regex_match('*') }}", payload)


def test_apply_jinja_template_regex_search():
    payload = {"name": "test"}

    assert apply_jinja_template("{{ payload.name | regex_search('.*') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('tes') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('est') }}", payload) == "True"
    assert apply_jinja_template("{{ payload.name | regex_search('test1') }}", payload) == "False"

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
