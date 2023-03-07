import json

import pytest
from django.conf import settings

from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


def test_apply_jinja_template():
    payload = {"name": "test"}
    rendered = apply_jinja_template("{{ payload | tojson_pretty }}", payload)
    result = json.loads(rendered)
    assert payload == result


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
