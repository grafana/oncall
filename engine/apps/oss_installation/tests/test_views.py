import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.oss_installation.models import CloudConnector


@pytest.mark.django_db
def test_cloud_connection_viewer_can_read(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    client = APIClient()
    url = reverse("oss_installation:cloud-connection-status")

    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_cloud_connection_viewer_cant_delete(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.VIEWER)

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    client = APIClient()
    url = reverse("oss_installation:cloud-connection-status")
    response = client.delete(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN
