from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.base.messaging import BaseMessagingBackend


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_template_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.pk})
    with patch(
        "apps.api.views.alert_receive_channel_template.AlertReceiveChannelTemplateView.update",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == expected_status

        response = client.patch(url, format="json", **make_user_auth_headers(user, token))
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_receive_channel_template_detail_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.pk})

    with patch(
        "apps.api.views.alert_receive_channel_template.AlertReceiveChannelTemplateView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_alert_receive_channel_template_include_additional_backend_templates(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        messaging_backends_templates={"TESTONLY": {"title": "the-title", "message": "the-message", "image_url": "url"}},
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    templates_data = response.json()
    assert templates_data["testonly_title_template"] == "the-title"
    assert templates_data["testonly_message_template"] == "the-message"
    assert templates_data["testonly_image_url_template"] == "url"


@pytest.mark.django_db
def test_alert_receive_channel_template_include_additional_backend_templates_using_defaults(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates=None)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    templates_data = response.json()
    assert templates_data["testonly_title_template"] == alert_receive_channel.get_default_template_attribute(
        "TESTONLY", "title"
    )
    assert templates_data["testonly_message_template"] == alert_receive_channel.get_default_template_attribute(
        "TESTONLY", "message"
    )
    assert templates_data["testonly_image_url_template"] == alert_receive_channel.get_default_template_attribute(
        "TESTONLY", "image_url"
    )


@pytest.mark.django_db
def test_update_alert_receive_channel_backend_template_invalid_template(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates=None)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    response = client.put(
        url, format="json", data={"testonly_title_template": "{{ wrong"}, **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"testonly_title_template": "invalid template"}


@pytest.mark.django_db
def test_update_alert_receive_channel_backend_template_invalid_url(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates=None)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    response = client.put(
        url, format="json", data={"testonly_image_url_template": "not-url"}, **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"testonly_image_url_template": "invalid URL"}


@pytest.mark.django_db
def test_update_alert_receive_channel_backend_template_empty_values_allowed(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates=None)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    response = client.put(
        url,
        format="json",
        data={"testonly_title_template": "", "testonly_image_url_template": ""},
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    alert_receive_channel.refresh_from_db()
    assert alert_receive_channel.messaging_backends_templates["TESTONLY"] == {"title": "", "image_url": ""}


@pytest.mark.django_db
def test_update_alert_receive_channel_backend_template_update_values(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        messaging_backends_templates={
            "TESTONLY": {"title": "the-title", "message": "some-message"},
            "OTHER": {"title": "some-title"},
        },
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel_template-detail", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    # patch messaging backends to add OTHER as a valid backend
    with patch(
        "apps.api.serializers.alert_receive_channel.get_messaging_backends",
        return_value=[("TESTONLY", BaseMessagingBackend), ("OTHER", BaseMessagingBackend)],
    ):
        response = client.put(
            url, format="json", data={"testonly_title_template": "updated-title"}, **make_user_auth_headers(user, token)
        )

    assert response.status_code == status.HTTP_200_OK
    alert_receive_channel.refresh_from_db()
    assert alert_receive_channel.messaging_backends_templates["TESTONLY"] == {
        "title": "updated-title",
        "message": "some-message",
    }
    assert alert_receive_channel.messaging_backends_templates["OTHER"] == {"title": "some-title"}


@pytest.mark.django_db
def test_preview_alert_receive_channel_backend_templater(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=default_channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={"title": "alert!"})
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-preview-template", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    data = {
        "template_body": "title: {{ payload.title }}",
        "template_name": "testonly_title_template",
    }
    response = client.post(url, format="json", data=data, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"preview": "title: alert!"}
