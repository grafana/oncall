from common.utils import clean_markup


def test_clean_code_blocks_name():
    original = "Tada! ```Tadada!``` `Tadadada!`"
    expected = "Tada! Tadada! Tadadada!"
    assert clean_markup(original) == expected


def test_clean_visual_basics():
    original = "~Stroke~ *Bold* _Italic_ ~Word ~"
    expected = "Stroke Bold Italic ~Word ~"
    assert clean_markup(original) == expected


def test_clean_block_quotes():
    original = (
        "This is unquoted text\n"
        "&gt; This is quoted text\n"
        "&gt; This is still quoted text\n"
        "This is unquoted text again"
    )
    expected = (
        "This is unquoted text\n"
        "> This is quoted text\n"
        "> This is still quoted text\n"
        "This is unquoted text again"
    )

    assert clean_markup(original) == expected


def test_clean_link():
    original = "<http://www.foo.com>"
    expected = "http://www.foo.com"
    assert clean_markup(original) == expected


def test_clean_mailto():
    # email
    original = "<mailto:bob@example.com>"
    expected = "bob@example.com"

    assert clean_markup(original) == expected
