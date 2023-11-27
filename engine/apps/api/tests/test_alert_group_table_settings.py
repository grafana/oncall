import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.user_management.constants import AlertGroupTableColumnTypeChoices
from apps.user_management.utils import alert_group_table_user_settings, default_columns

DEFAULT_COLUMNS = default_columns()


def columns_settings(add_column=None):
    default_settings = {"visible": DEFAULT_COLUMNS[:], "hidden": []}
    if add_column:
        default_settings["hidden"].append(add_column)
    return default_settings


@pytest.mark.django_db
def test_get_columns(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_result = alert_group_table_user_settings(user)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "initial_columns_settings,updated_columns_settings,status_code",
    [
        # add column
        (
            columns_settings(),
            columns_settings({"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}),
            status.HTTP_200_OK,
        ),
        # remove column
        (
            columns_settings({"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}),
            columns_settings(),
            status.HTTP_200_OK,
        ),
        # wrong data format
        (columns_settings(), {}, status.HTTP_400_BAD_REQUEST),
        (columns_settings(), {"visible": []}, status.HTTP_400_BAD_REQUEST),
        (columns_settings(), {"hidden": []}, status.HTTP_400_BAD_REQUEST),
        # wrong id
        (
            columns_settings(),
            columns_settings({"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.DEFAULT.value}),
            status.HTTP_400_BAD_REQUEST,
        ),
        # duplicate id
        (
            columns_settings(),
            columns_settings({"name": "Test", "id": 1, "type": AlertGroupTableColumnTypeChoices.DEFAULT.value}),
            status.HTTP_400_BAD_REQUEST,
        ),
        # remove default column
        (
            columns_settings(),
            {"visible": DEFAULT_COLUMNS[:-1], "hidden": []},
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
@pytest.mark.django_db
def test_update_columns_list(
    initial_columns_settings,
    updated_columns_settings,
    status_code,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """Test alert group table settings for organization (POST request)"""
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    client.post(url, data=initial_columns_settings, format="json", **make_user_auth_headers(user, token))
    response = client.post(url, data=updated_columns_settings, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json() == updated_columns_settings


@pytest.mark.parametrize(
    "initial_columns_settings,updated_columns_settings,status_code",
    [
        # hide column
        (columns_settings(), {"visible": DEFAULT_COLUMNS[:-1], "hidden": DEFAULT_COLUMNS[-1:]}, status.HTTP_200_OK),
        # make column visible
        ({"visible": DEFAULT_COLUMNS[:-1], "hidden": DEFAULT_COLUMNS[-1:]}, columns_settings(), status.HTTP_200_OK),
        # wrong data format
        (columns_settings(), {}, status.HTTP_400_BAD_REQUEST),
        (columns_settings(), {"visible": []}, status.HTTP_400_BAD_REQUEST),
        (columns_settings(), {"hidden": []}, status.HTTP_400_BAD_REQUEST),
        # hide all columns
        (columns_settings(), {"visible": [], "hidden": DEFAULT_COLUMNS[:]}, status.HTTP_400_BAD_REQUEST),
        # add column
        (
            columns_settings(),
            columns_settings({"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}),
            status.HTTP_400_BAD_REQUEST,
        ),
        # remove column
        (
            columns_settings({"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}),
            columns_settings(),
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
@pytest.mark.django_db
def test_update_columns_settings(
    initial_columns_settings,
    updated_columns_settings,
    status_code,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """Test alert group table settings for user (PUT request)"""
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    client.post(url, data=initial_columns_settings, format="json", **make_user_auth_headers(user, token))
    response = client.put(url, data=updated_columns_settings, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json() == updated_columns_settings


@pytest.mark.django_db
def test_reset_user_columns(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """Test reset alert group table settings for user"""
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:alert_group_table-reset_columns_settings")
    new_column = {"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}
    organization.alert_group_table_columns += [new_column]
    organization.save()
    user.update_alert_group_table_columns_settings(organization.alert_group_table_columns[1::-1])
    default_settings = columns_settings(new_column)
    assert alert_group_table_user_settings(user) != default_settings
    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == default_settings


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_get_columns_permissions(
    role,
    expected_status,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_update_columns_list_permissions(
    role,
    expected_status,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    data = columns_settings()
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_update_columns_settings_permissions(
    role,
    expected_status,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:alert_group_table-columns_settings")
    data = columns_settings()
    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_reset_user_columns_permissions(
    role,
    expected_status,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:alert_group_table-reset_columns_settings")
    response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
