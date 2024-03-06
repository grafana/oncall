from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import ResolutionNote
from apps.auth_token.auth import GRAFANA_SA_PREFIX, ApiTokenAuthentication, GrafanaServiceAccountAuthentication
from apps.auth_token.models import ApiAuthToken


@pytest.mark.django_db
def test_get_resolution_notes(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group_1 = make_alert_group(alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel)

    resolution_note_1 = make_resolution_note(
        alert_group=alert_group_1,
        source=ResolutionNote.Source.WEB,
        author=user,
    )
    resolution_note_2 = make_resolution_note(
        alert_group=alert_group_2,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-public:resolution_notes-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_response = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": resolution_note_2.public_primary_key,
                "alert_group_id": alert_group_2.public_primary_key,
                "author": user.public_primary_key,
                "source": resolution_note_2.get_source_display(),
                "created_at": resolution_note_2.created_at.isoformat().replace("+00:00", "Z"),
                "text": resolution_note_2.text,
            },
            {
                "id": resolution_note_1.public_primary_key,
                "alert_group_id": alert_group_1.public_primary_key,
                "author": user.public_primary_key,
                "source": resolution_note_1.get_source_display(),
                "created_at": resolution_note_1.created_at.isoformat().replace("+00:00", "Z"),
                "text": resolution_note_1.text,
            },
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_resolution_note(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": resolution_note.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": resolution_note.public_primary_key,
        "alert_group_id": alert_group.public_primary_key,
        "author": user.public_primary_key,
        "source": resolution_note.get_source_display(),
        "created_at": response.data["created_at"],
        "text": resolution_note.text,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == result


@pytest.mark.django_db
def test_create_resolution_note(make_organization_and_user_with_token, make_alert_receive_channel, make_alert_group):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    url = reverse("api-public:resolution_notes-list")

    data = {
        "alert_group_id": alert_group.public_primary_key,
        "text": "Test Resolution Note Message",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    resolution_note = ResolutionNote.objects.get(public_primary_key=response.data["id"])

    result = {
        "id": resolution_note.public_primary_key,
        "alert_group_id": alert_group.public_primary_key,
        "author": user.public_primary_key,
        "source": resolution_note.get_source_display(),
        "created_at": response.data["created_at"],
        "text": data["text"],
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == result


@pytest.mark.django_db
def test_create_resolution_note_invalid_text(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    url = reverse("api-public:resolution_notes-list")

    data = {
        "alert_group_id": alert_group.public_primary_key,
        "text": "",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["text"][0] == "This field may not be blank."


@pytest.mark.django_db
def test_update_resolution_note(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": resolution_note.public_primary_key})

    data = {
        "text": "Test Resolution Note Message",
    }

    assert resolution_note.text != data["text"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    result = {
        "id": resolution_note.public_primary_key,
        "alert_group_id": alert_group.public_primary_key,
        "author": user.public_primary_key,
        "source": resolution_note.get_source_display(),
        "created_at": response.data["created_at"],
        "text": data["text"],
    }

    assert response.status_code == status.HTTP_200_OK
    resolution_note.refresh_from_db()
    assert resolution_note.text == result["text"]
    assert response.data == result


@pytest.mark.django_db
def test_update_resolution_note_invalid_source(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.SLACK,
        author=user,
    )

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": resolution_note.public_primary_key})

    data = {
        "text": "Test Resolution Note Message",
    }

    assert resolution_note.message_text != data["text"]

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    resolution_note.refresh_from_db()
    assert resolution_note.message_text != data["text"]
    assert response.data["detail"] == "Cannot update message with this source type"


@pytest.mark.django_db
def test_delete_resolution_note(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    resolution_note = make_resolution_note(
        alert_group=alert_group,
        source=ResolutionNote.Source.WEB,
        author=user,
    )

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": resolution_note.public_primary_key})

    assert resolution_note.deleted_at is None

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    resolution_note.refresh_from_db()

    assert resolution_note.deleted_at is not None

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "Not found."


@pytest.mark.django_db
def test_create_resolution_note_grafana_auth(make_organization_and_user, make_alert_receive_channel, make_alert_group):
    organization, user = make_organization_and_user()
    client = APIClient()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    url = reverse("api-public:resolution_notes-list")

    data = {
        "alert_group_id": alert_group.public_primary_key,
        "text": "Test Resolution Note Message",
    }

    api_token_auth = ApiTokenAuthentication()
    grafana_sa_auth = GrafanaServiceAccountAuthentication()

    # GrafanaServiceAccountAuthentication handles empty auth
    with patch(
        "apps.auth_token.auth.ApiTokenAuthentication.authenticate", wraps=api_token_auth.authenticate
    ) as mock_api_key_auth, patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate", wraps=grafana_sa_auth.authenticate
    ) as mock_grafana_auth:
        response = client.post(url, data=data, format="json")
        mock_grafana_auth.assert_called_once()
        mock_api_key_auth.assert_not_called()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    token = "abc123"
    # GrafanaServiceAccountAuthentication passes through api key auth
    with patch(
        "apps.auth_token.auth.ApiTokenAuthentication.authenticate", wraps=api_token_auth.authenticate
    ) as mock_api_key_auth, patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate", wraps=grafana_sa_auth.authenticate
    ) as mock_grafana_auth:
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
        mock_grafana_auth.assert_called_once()
        mock_api_key_auth.assert_called_once()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    token = f"{GRAFANA_SA_PREFIX}123"
    # GrafanaServiceAccountAuthentication handle invalid token
    with patch(
        "apps.auth_token.auth.ApiTokenAuthentication.authenticate", wraps=api_token_auth.authenticate
    ) as mock_api_key_auth, patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate", wraps=grafana_sa_auth.authenticate
    ) as mock_grafana_auth:
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
        mock_grafana_auth.assert_called_once()
        mock_api_key_auth.assert_not_called()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    success_token = ApiAuthToken(organization=organization, user=user, name="Grafana Service Account")
    # GrafanaServiceAccountAuthentication handle successful token
    with patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate", return_value=(user, success_token)
    ):
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
        assert response.status_code == status.HTTP_201_CREATED
        resolution_note = ResolutionNote.objects.get(public_primary_key=response.data["id"])
        result = {
            "id": resolution_note.public_primary_key,
            "alert_group_id": alert_group.public_primary_key,
            "author": user.public_primary_key,
            "source": resolution_note.get_source_display(),
            "created_at": response.data["created_at"],
            "text": data["text"],
        }
        assert response.data == result
