import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import CustomButton
from common.constants.role import Role

TEST_URL = "https://amixr.io"


@pytest.fixture()
def custom_button_internal_api_setup(make_organization_and_user_with_plugin_token, make_custom_action):
    organization, user, token = make_organization_and_user_with_plugin_token()
    custom_button = make_custom_action(
        name="github_button",
        webhook="https://github.com/",
        user="Chris Vanstras",
        password="qwerty",
        data='{"name": "{{ alert_payload }}"}',
        authorization_header="auth_token",
        organization=organization,
    )
    return user, token, custom_button


@pytest.mark.django_db
def test_get_list_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    expected_payload = [
        {
            "id": custom_button.public_primary_key,
            "name": "github_button",
            "team": None,
            "webhook": "https://github.com/",
            "data": '{"name": "{{ alert_payload }}"}',
            "user": "Chris Vanstras",
            "password": "qwerty",
            "authorization_header": "auth_token",
            "forward_whole_payload": False,
        }
    ]

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_detail_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    expected_payload = {
        "id": custom_button.public_primary_key,
        "name": "github_button",
        "team": None,
        "webhook": "https://github.com/",
        "data": '{"name": "{{ alert_payload }}"}',
        "user": "Chris Vanstras",
        "password": "qwerty",
        "authorization_header": "auth_token",
        "forward_whole_payload": False,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_create_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button",
        "webhook": TEST_URL,
        "team": None,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    custom_button = CustomButton.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": custom_button.public_primary_key,
        "user": None,
        "password": None,
        "data": None,
        "authorization_header": None,
        "forward_whole_payload": False,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == expected_response


@pytest.mark.django_db
def test_create_valid_data_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_with_valid_data",
        "webhook": TEST_URL,
        "data": '{"name": "{{ alert_payload }}"}',
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    custom_button = CustomButton.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": custom_button.public_primary_key,
        "user": None,
        "password": None,
        "authorization_header": None,
        "forward_whole_payload": False,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_valid_nested_data_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_with_valid_data",
        "webhook": TEST_URL,
        # Assert that nested field access still works as long as the variable
        # is quoted, making it valid JSON.
        # This ensures backwards compatibility from when templates were required
        # to be JSON.
        "data": '{"nested_item": "{{ alert_payload.foo.bar }}"}',
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    custom_button = CustomButton.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": custom_button.public_primary_key,
        "user": None,
        "password": None,
        "authorization_header": None,
        "forward_whole_payload": False,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_valid_data_after_render_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_with_valid_data",
        "webhook": TEST_URL,
        "data": '{"name": "{{ alert_payload.name }}", "labels": {{ alert_payload.labels | tojson }}}',
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    custom_button = CustomButton.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": custom_button.public_primary_key,
        "user": None,
        "password": None,
        "authorization_header": None,
        "forward_whole_payload": False,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_valid_data_after_render_use_all_data_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_with_valid_data",
        "webhook": TEST_URL,
        "data": "{{ alert_payload | tojson }}",
        "team": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    # modify initial data by adding id and None for optional fields
    custom_button = CustomButton.objects.get(public_primary_key=response.data["id"])
    expected_response = data | {
        "id": custom_button.public_primary_key,
        "user": None,
        "password": None,
        "authorization_header": None,
        "forward_whole_payload": False,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_invalid_url_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_invalid_url",
        "webhook": "invalid_url",
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_invalid_data_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_invalid_data",
        "webhook": TEST_URL,
        "data": "invalid_json",
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_invalid_templated_data_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-list")

    data = {
        "name": "amixr_button_invalid_data",
        "webhook": TEST_URL,
        # This would need a `| tojson` or some double quotes around it to pass validation.
        "data": "{{ alert_payload.name }}",
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    data = {
        "name": "github_button_updated",
        "webhook": "https://github.com/",
        "team": None,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = CustomButton.objects.get(public_primary_key=custom_button.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.name == "github_button_updated"


@pytest.mark.django_db
def test_delete_custom_button(custom_button_internal_api_setup, make_user_auth_headers):
    user, token, custom_button = custom_button_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_custom_button_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_action,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:custom_button-list")

    with patch(
        "apps.api.views.custom_button.CustomButtonView.create",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_custom_button_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_action,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    custom_button = make_custom_action(organization=organization)
    client = APIClient()

    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    with patch(
        "apps.api.views.custom_button.CustomButtonView.update",
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
    [(Role.ADMIN, status.HTTP_200_OK), (Role.EDITOR, status.HTTP_200_OK), (Role.VIEWER, status.HTTP_200_OK)],
)
def test_custom_button_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_action,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    make_custom_action(organization=organization)
    client = APIClient()

    url = reverse("api-internal:custom_button-list")

    with patch(
        "apps.api.views.custom_button.CustomButtonView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [(Role.ADMIN, status.HTTP_200_OK), (Role.EDITOR, status.HTTP_200_OK), (Role.VIEWER, status.HTTP_200_OK)],
)
def test_custom_button_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_action,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    custom_button = make_custom_action(organization=organization)
    client = APIClient()

    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    with patch(
        "apps.api.views.custom_button.CustomButtonView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_204_NO_CONTENT),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_custom_button_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_custom_action,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    custom_button = make_custom_action(organization=organization)
    client = APIClient()

    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    with patch(
        "apps.api.views.custom_button.CustomButtonView.destroy",
        return_value=Response(
            status=status.HTTP_204_NO_CONTENT,
        ),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_get_custom_button_from_other_team_with_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    custom_button = make_custom_action(organization=organization, team=team)
    client = APIClient()

    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})
    url = f"{url}?from_organization=true"

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_custom_button_from_other_team_without_flag(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_custom_action,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    team = make_team(organization)

    custom_button = make_custom_action(organization=organization, team=team)
    client = APIClient()

    url = reverse("api-internal:custom_button-detail", kwargs={"pk": custom_button.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN
