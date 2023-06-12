import pytest

from common.utils import urlize_with_respect_to_a


def test_urlize_will_not_mutate_text_without_links():
    original = "Text without link"
    expected = original
    assert urlize_with_respect_to_a(original) == expected


def test_urlize_will_not_mutate_text_with_link_in_a():
    original = '<a href="https://amixr.io/">amixr website</a>'
    expected = original
    assert urlize_with_respect_to_a(original) == expected


@pytest.mark.filterwarnings(
    "ignore:The input looks more like a URL than markup. You may want to use an HTTP client like requests to get the "
    "document behind the URL, and feed that document to Beautiful Soup."
)
def test_urlize_will_wrap_link():
    original = "https://amixr.io/"
    expected = '<a href="https://amixr.io/">https://amixr.io/</a>'
    assert urlize_with_respect_to_a(original) == expected


def test_urlize_will_not_wrap_link_inside_a():
    original = '<a href="https://amixr.io/">https://amixr.io/</a>'
    expected = original
    assert urlize_with_respect_to_a(original) == expected
