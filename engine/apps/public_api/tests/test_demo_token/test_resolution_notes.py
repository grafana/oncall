import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import ResolutionNote
from apps.public_api import constants as public_api_constants

demo_resolution_note_payload = {
    "id": public_api_constants.DEMO_RESOLUTION_NOTE_ID,
    "alert_group_id": public_api_constants.DEMO_INCIDENT_ID,
    "author": public_api_constants.DEMO_USER_ID,
    "source": public_api_constants.DEMO_RESOLUTION_NOTE_SOURCE,
    "created_at": public_api_constants.DEMO_RESOLUTION_NOTE_CREATED_AT,
    "text": public_api_constants.DEMO_RESOLUTION_NOTE_TEXT,
}

demo_resolution_note_payload_list = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [demo_resolution_note_payload],
}


@pytest.mark.django_db
def test_demo_get_resolution_note_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:resolution_notes-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_resolution_note_payload_list


@pytest.mark.django_db
def test_demo_get_resolution_note(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": public_api_constants.DEMO_RESOLUTION_NOTE_ID})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_resolution_note_payload


@pytest.mark.django_db
def test_demo_post_resolution_note(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:resolution_notes-list")

    data = {"alert_group_id": public_api_constants.DEMO_INCIDENT_ID, "text": "New demo text"}

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == demo_resolution_note_payload


@pytest.mark.django_db
def test_demo_update_resolution_note(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    data = {"alert_group_id": public_api_constants.DEMO_INCIDENT_ID, "text": "Updated demo text"}

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": public_api_constants.DEMO_RESOLUTION_NOTE_ID})

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_resolution_note_payload


@pytest.mark.django_db
def test_demo_delete_resolution_note(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:resolution_notes-detail", kwargs={"pk": public_api_constants.DEMO_RESOLUTION_NOTE_ID})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ResolutionNote.objects.filter(public_primary_key=public_api_constants.DEMO_RESOLUTION_NOTE_ID).exists()
