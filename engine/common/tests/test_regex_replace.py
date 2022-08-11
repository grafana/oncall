from common.jinja_templater.filters import regex_replace


def test_regex_replace_drop_field():
    original = "[ var='D0' metric='my_metric' labels={} value=140 ]"
    expected = "[ metric='my_metric' labels={} value=140 ]"
    assert regex_replace(original, "var='[a-zA-Z0-9]+' ", "") == expected
