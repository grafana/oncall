from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from common.api_helpers.custom_ratelimit import load_custom_ratelimits


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


@pytest.mark.django_db
def test_custom_throttling(make_organization_and_user_with_token):
    organization_with_custom_ratelimit, _, token_with_custom_ratelimit = make_organization_and_user_with_token()
    _, _, token_with_default_ratelimit = make_organization_and_user_with_token()
    cache.clear()

    CUSTOM_RATELIMITS_STR = (
        '{"'
        + str(organization_with_custom_ratelimit.pk)
        + '": {"integration": "10/5m","organization": "15/5m","public_api": "1/m"}}'
    )

    with override_settings(CUSTOM_RATELIMITS=load_custom_ratelimits(CUSTOM_RATELIMITS_STR)):
        client = APIClient()

        url = reverse("api-public:alert_groups-list")

        # Organization without custom ratelimit should use default ratelimit
        for _ in range(5):
            response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token_with_default_ratelimit}")
            assert response.status_code == status.HTTP_200_OK

        # Organization with custom ratelimit will be ratelimited after 1 request
        response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token_with_custom_ratelimit}")

        assert response.status_code == status.HTTP_200_OK

        response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token_with_custom_ratelimit}")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # make sure RateLimitHeadersMixin used
        assert response.has_header("RateLimit-Reset")
