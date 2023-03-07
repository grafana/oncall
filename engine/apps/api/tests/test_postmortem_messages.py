from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import ResolutionNote
from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_create_resolution_note(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_alert_receive_channel, make_alert_group
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    url = reverse("api-internal:resolution_note-list")

    data = {
        "alert_group": alert_group.public_primary_key,
        "text": "Test Message",
    }

    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    resolution_note = ResolutionNote.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": resolution_note.public_primary_key,
        "alert_group": alert_group.public_primary_key,
        "source": {
            "id": resolution_note.source,
            "display_name": resolution_note.get_source_display(),
        },
        "author": {
            "pk": user.public_primary_key,
            "username": user.username,
        },
        "created_at": response.data["created_at"],
        "text": data["text"],
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == result


@pytest.mark.django_db
def test_create_resolution_note_invalid_text(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    url = reverse("api-internal:resolution_note-list")

    data = {
        "alert_group": alert_group.public_primary_key,
        "text": "",
    }

    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["text"][0] == "This field may not be blank."


@pytest.mark.django_db
def test_update_resolution_note(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    data = {
        "text": "Test Message",
    }

    assert resolution_note.text != data["text"]

    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    result = {
        "id": resolution_note.public_primary_key,
        "alert_group": alert_group.public_primary_key,
        "source": {
            "id": resolution_note.source,
            "display_name": resolution_note.get_source_display(),
        },
        "author": {
            "pk": user.public_primary_key,
            "username": user.username,
        },
        "created_at": response.data["created_at"],
        "text": data["text"],
    }

    assert response.status_code == status.HTTP_200_OK
    resolution_note.refresh_from_db()
    assert resolution_note.text == result["text"]
    assert response.data == result


@pytest.mark.django_db
def test_update_resolution_note_invalid_source(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.SLACK,
        author=user,
    )

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    data = {
        "text": "Test Message",
    }

    assert resolution_note.message_text != data["text"]

    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    resolution_note.refresh_from_db()
    assert resolution_note.message_text != data["text"]
    assert response.data["detail"] == "Cannot update message with this source type"


@pytest.mark.django_db
def test_delete_resolution_note(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    assert resolution_note.deleted_at is None

    response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_204_NO_CONTENT

    resolution_note.refresh_from_db()

    assert resolution_note.deleted_at is not None

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "Not found."


@patch(
    "apps.api.views.resolution_note.ResolutionNoteView.create",
    return_value=Response(
        status=status.HTTP_200_OK,
        data={},  # mock data with empty dict to satisfy overridden dispatch method in ResolutionNoteView
    ),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_resolution_note_create_permissions(
    mocked_create,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:resolution_note-list")

    response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@patch(
    "apps.api.views.resolution_note.ResolutionNoteView.update",
    return_value=Response(
        status=status.HTTP_200_OK,
        data={},  # mock data with empty dict to satisfy overridden dispatch method in ResolutionNoteView
    ),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_resolution_note_update_permissions(
    mocked_update,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )
    client = APIClient()

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    response = client.put(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status

    response = client.patch(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@patch(
    "apps.api.views.resolution_note.ResolutionNoteView.destroy",
    return_value=Response(status=status.HTTP_204_NO_CONTENT, data={}),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_resolution_note_delete_permissions(
    mocked_delete,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )
    client = APIClient()

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@patch(
    "apps.api.views.resolution_note.ResolutionNoteView.list",
    return_value=Response(
        status=status.HTTP_200_OK,
    ),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_resolution_note_list_permissions(
    mocked_list,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:resolution_note-list")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@patch(
    "apps.api.views.resolution_note.ResolutionNoteView.retrieve",
    return_value=Response(
        status=status.HTTP_200_OK,
    ),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_resolution_note_detail_permissions(
    mocked_detail,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )
    client = APIClient()

    url = reverse("api-internal:resolution_note-detail", kwargs={"pk": resolution_note.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
