import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.mobile_app.models import MobileAppAuthToken


@pytest.mark.django_db
def test_mobile_app_auth_token(
    make_organization_and_user_with_mobile_app_verification_token,
):
    organization, user, verification_token = make_organization_and_user_with_mobile_app_verification_token()

    client = APIClient()
    url = reverse("mobile_app:auth_token")

    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.post(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_201_CREATED

    original_auth_token_id = response.data["id"]
    original_auth_token = response.data["token"]
    original_auth_token_created_at = response.data["created_at"]

    assert original_auth_token_id is not None
    assert original_auth_token is not None
    assert original_auth_token_created_at is not None

    # we can fetch the token
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.get(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_200_OK

    assert response.data["token_id"] == original_auth_token_id
    assert response.data["user_id"] == user.id
    assert response.data["organization_id"] == organization.id
    assert response.data["created_at"] == original_auth_token_created_at
    assert response.data["revoked_at"] is None

    # can only ever have one mobile app auth token.. old one gets deleted if we try
    # creating a new one
    response = client.post(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_201_CREATED

    new_auth_token_id = response.data["id"]
    new_auth_token = response.data["token"]
    new_auth_token_created_at = response.data["created_at"]

    assert new_auth_token_id is not None
    assert new_auth_token is not None
    assert new_auth_token_created_at is not None

    assert new_auth_token_id != original_auth_token_id
    assert new_auth_token != original_auth_token
    assert new_auth_token_created_at != original_auth_token_created_at

    assert MobileAppAuthToken.objects.filter(user=user).count() == 1

    # we can delete the token
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.delete(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert MobileAppAuthToken.objects.filter(user=user).count() == 0

    response = client.delete(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.get(url, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
