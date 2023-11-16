import pytest
import yaml
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
@override_settings(DRF_SPECTACULAR_ENABLED=True)
def test_fetching_the_openapi_schema_works(settings, reload_urls):
    reload_urls()

    client = APIClient()
    response = client.get(reverse("schema"))

    assert response.status_code == status.HTTP_200_OK
    assert yaml.safe_load(response.content)["info"]["title"] == settings.SPECTACULAR_SETTINGS["TITLE"]
