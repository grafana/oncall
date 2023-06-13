from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_throttling(make_organization_and_user_with_token):
    with patch("apps.public_api.throttlers.user_throttle.UserThrottle.rate", new_callable=PropertyMock) as mocked_rate:
        mocked_rate.return_value = "1/m"

        _, _, token = make_organization_and_user_with_token()
        cache.clear()

        client = APIClient()

        url = reverse("api-public:alert_groups-list")

        response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

        assert response.status_code == status.HTTP_200_OK

        response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # make sure RateLimitHeadersMixin used
        assert response.has_header("RateLimit-Reset")
