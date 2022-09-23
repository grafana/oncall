from apps.schedules.ical_utils import parse_username_from_string


def test_one_username():
    assert parse_username_from_string("bob") == "bob"


def test_mixed_languages_username():
    assert parse_username_from_string("bobиванtannhäuser夕海") == "bobиванtannhäuser夕海"


def test_username_with_spaces():
    assert parse_username_from_string("bob smith") == "bob smith"
    assert parse_username_from_string(" bob smith ") == "bob smith"


def test_username_with_hyphen():
    assert parse_username_from_string("bob-smith") == "bob-smith"


def test_username_with_punctiation():
    assert parse_username_from_string("bob-smith") == "bob-smith"
    assert parse_username_from_string("bob.smith") == "bob.smith"
    assert parse_username_from_string("bob'smith") == "bob'smith"
    assert parse_username_from_string("bob;smith") == "bob;smith"
    assert parse_username_from_string("bob,smith") == "bob,smith"
    assert parse_username_from_string("bob/smith") == "bob/smith"
    assert parse_username_from_string("bob)([]{}") == "bob)([]{}"


def test_non_space_delimiter():
    assert parse_username_from_string("@bob:@alex") == "@bob:@alex"
    assert parse_username_from_string("@bob@@alex") == "@bob@@alex"
    assert parse_username_from_string("@bob@alex") == "@bob@alex"


def test_numeric_username():
    assert parse_username_from_string("bob1") == "bob1"
    assert parse_username_from_string("1") == "1"


def test_email_address_username():
    assert parse_username_from_string("bob@bob.com") == "bob@bob.com"


def test_grafana_username():
    assert parse_username_from_string("!@#%^&*()_+[];',./\\|") == "!@#%^&*()_+[];',./\\|"


def test_remove_priority_from_username():
    assert parse_username_from_string("[L1]bob") == "bob"
    assert parse_username_from_string("[L1] bob") == "bob"
    assert parse_username_from_string(" [L1] bob ") == "bob"
    assert parse_username_from_string("[L2] bob[L1]") == "bob[L1]"
    assert parse_username_from_string("[L27]bob") == "bob"
    assert parse_username_from_string("[[L2]] bob[[[L1]") == "[[L2]] bob[[[L1]"
