from django.test.utils import override_settings

from common.api_helpers.utils import create_engine_url


@override_settings(BASE_URL="http://localhost:8000")
def test_create_engine_url_no_slash():
    assert create_engine_url("destination") == "http://localhost:8000/destination"
    assert create_engine_url("/destination") == "http://localhost:8000/destination"
    assert create_engine_url("destination/") == "http://localhost:8000/destination/"
    assert create_engine_url("/destination/") == "http://localhost:8000/destination/"


@override_settings(BASE_URL="http://localhost:8000/")
def test_create_engine_url_slash():
    assert create_engine_url("destination") == "http://localhost:8000/destination"
    assert create_engine_url("/destination") == "http://localhost:8000/destination"
    assert create_engine_url("destination/") == "http://localhost:8000/destination/"
    assert create_engine_url("/destination/") == "http://localhost:8000/destination/"


@override_settings(BASE_URL="http://localhost:8000/test123")
def test_create_engine_url_prefix_no_slash():
    assert create_engine_url("destination") == "http://localhost:8000/test123/destination"
    assert create_engine_url("/destination") == "http://localhost:8000/test123/destination"
    assert create_engine_url("destination/") == "http://localhost:8000/test123/destination/"
    assert create_engine_url("/destination/") == "http://localhost:8000/test123/destination/"


@override_settings(BASE_URL="http://localhost:8000/test123/")
def test_create_engine_url_prefix_slash():
    assert create_engine_url("destination") == "http://localhost:8000/test123/destination"
    assert create_engine_url("/destination") == "http://localhost:8000/test123/destination"
    assert create_engine_url("destination/") == "http://localhost:8000/test123/destination/"
    assert create_engine_url("/destination/") == "http://localhost:8000/test123/destination/"
