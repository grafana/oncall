import pytest

from apps.base.messaging import get_messaging_backend_from_id, get_messaging_backends


@pytest.mark.django_db
def test_messaging_backends_disabled(settings):
    settings.FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED = False

    assert get_messaging_backends() == {}
    assert get_messaging_backend_from_id("TESTONLY") is None


@pytest.mark.django_db
def test_messaging_backends_enabled(settings):
    settings.FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED = True

    assert get_messaging_backends() != {}
    assert get_messaging_backend_from_id("TESTONLY") is not None
