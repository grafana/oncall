from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@patch("apps.public_api.throttlers.user_throttle.UserThrottle.get_throttle_limits")
@pytest.mark.django_db
def test_throttling(mocked_throttle_limits, make_organization_and_user_with_token):
    MAX_REQUESTS = 1
    PERIOD = 360

    _, _, token = make_organization_and_user_with_token()
    cache.clear()

    client = APIClient()

    mocked_throttle_limits.return_value = MAX_REQUESTS, PERIOD
    url = reverse("api-public:alert_groups-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # make sure RateLimitHeadersMixin used
    assert response.has_header("RateLimit-Reset")
