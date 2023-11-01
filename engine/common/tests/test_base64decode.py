from common.jinja_templater.filters import b64decode


def test_base64_encode():
    original = "dGVzdCBlbmNvZGUgc3RyaW5n"
    expected = "test encode string"
    assert b64decode(original) == expected
