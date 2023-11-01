from common.jinja_templater.filters import b64decode


def test_base64_decode():
    original = "dGVzdCBzdHJpbmch"
    expected = "test string!"
    assert b64decode(original) == expected
