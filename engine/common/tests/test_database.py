from django.test import override_settings

from common.database import get_random_readonly_database_key_if_present_otherwise_default

MOCK_READ_ONLY_DATABASES = {
    "foo": "asdfkdjkdfjkdf",
    "bar": "nmcvnmcvmnvc",
}


class TestGetRandomReadOnlyDatabaseKeyIfPresentOtherwiseDefault:
    @override_settings(READONLY_DATABASES=MOCK_READ_ONLY_DATABASES)
    def test_it_randomly_chooses_a_readonly_database(self) -> None:
        assert get_random_readonly_database_key_if_present_otherwise_default() in MOCK_READ_ONLY_DATABASES

    @override_settings(READONLY_DATABASES={})
    def test_it_falls_back_to_default_if_readonly_databases_is_set_but_empty(self) -> None:
        assert get_random_readonly_database_key_if_present_otherwise_default() == "default"

    def test_it_falls_back_to_default_if_readonly_databases_is_not_set(self) -> None:
        assert get_random_readonly_database_key_if_present_otherwise_default() == "default"
