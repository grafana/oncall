import pytest

from apps.base.messaging import get_messaging_backend_from_id, get_messaging_backends


@pytest.mark.django_db
def test_messaging_backends_enabled(settings):
    assert get_messaging_backends() != {}
    assert get_messaging_backend_from_id("TESTONLY") is not None
