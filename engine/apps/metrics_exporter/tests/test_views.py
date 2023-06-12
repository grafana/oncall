import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.parametrize(
    "token,auth,expected",
    [
        (None, None, 200),
        ("secret", "invalid", 401),
        ("secret", "secret", 200),
    ],
)
@override_settings(FEATURE_PROMETHEUS_EXPORTER_ENABLED=True)
def test_metrics_exporter_auth(settings, reload_urls, token, auth, expected):
    reload_urls()

    settings.PROMETHEUS_EXPORTER_SECRET = token

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(auth))

    url = reverse("metrics-exporter")
    response = client.get(url)

    assert response.status_code == expected
