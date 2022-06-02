import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_preview_template_options_include_additional_backends(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    _, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse(
        "api-internal:preview_template_options",
    )
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert "testonly" in response.json()["notification_channel_options"]
