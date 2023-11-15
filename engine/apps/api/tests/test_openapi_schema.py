import pytest
import yaml
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_fetching_the_openapi_schema_works(settings):
    client = APIClient()
    response = client.get(reverse("schema"))

    assert response.status_code == status.HTTP_200_OK
    assert yaml.safe_load(response.content)["info"]["title"] == settings.SPECTACULAR_SETTINGS["TITLE"]
