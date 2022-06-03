from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.base.models import OrganizationLogRecord
from apps.user_management.organization_log_creator import OrganizationLogType
from common.constants.role import Role


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_organization_log_records_permissions(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, role, expected_status
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:organization_log-list")

    with patch(
        "apps.api.views.organization_log_record.OrganizationLogRecordView.list",
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_organization_log_records_filters_permissions(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, role, expected_status
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:organization_log-filters")

    with patch(
        "apps.api.views.organization_log_record.OrganizationLogRecordView.filters",
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
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_organization_log_records_label_options_permissions(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, role, expected_status
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:organization_log-label-options")

    with patch(
        "apps.api.views.organization_log_record.OrganizationLogRecordView.label_options",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_get_filter_created_at(
    make_organization_and_user_with_plugin_token,
    make_organization_log_record,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    make_organization_log_record(organization, user)

    url = reverse("api-internal:organization_log-list")
    response = client.get(
        url + "?created_at=1970-01-01T00:00:00/2099-01-01T23:59:59",
        format="json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_get_filter_created_at_empty_result(
    make_organization_and_user_with_plugin_token,
    make_organization_log_record,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    make_organization_log_record(organization, user)

    url = reverse("api-internal:organization_log-list")
    response = client.get(
        f"{url}?created_at=1970-01-01T00:00:00/1970-01-01T23:59:59",
        format="json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_created_at_invalid_format(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:organization_log-list")
    response = client.get(f"{url}?created_at=invalid_date_format", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.skip(reason="SQLITE Incompatibility")
@pytest.mark.django_db
def test_get_filter_by_labels(
    make_organization_and_user_with_plugin_token,
    make_organization_log_record,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    # create log that contains LABEL_SLACK and LABEL_DEFAULT_CHANNEL
    make_organization_log_record(organization, user, type=OrganizationLogType.TYPE_SLACK_DEFAULT_CHANNEL_CHANGED)
    # create log that contains LABEL_SLACK but does not contain LABEL_DEFAULT_CHANNEL
    make_organization_log_record(organization, user, type=OrganizationLogType.TYPE_SLACK_WORKSPACE_DISCONNECTED)
    # create log that does not contain labels from search
    make_organization_log_record(organization, user, type=OrganizationLogType.TYPE_INTEGRATION_CREATED)

    url = reverse("api-internal:organization_log-list")
    # search by one label: LABEL_SLACK
    response = client.get(
        f"{url}?labels={OrganizationLogRecord.LABEL_SLACK}", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    response_log_labels = [log["labels"] for log in response.data["results"]]
    for labels in response_log_labels:
        assert OrganizationLogRecord.LABEL_SLACK in labels

    # search by two labels: LABEL_SLACK and LABEL_DEFAULT_CHANNEL
    response = client.get(
        f"{url}?labels={OrganizationLogRecord.LABEL_SLACK}&labels={OrganizationLogRecord.LABEL_DEFAULT_CHANNEL}",
        format="json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    response_log_labels = [log["labels"] for log in response.data["results"]]
    for labels in response_log_labels:
        assert OrganizationLogRecord.LABEL_SLACK in labels
        assert OrganizationLogRecord.LABEL_DEFAULT_CHANNEL in labels


@pytest.mark.django_db
def test_get_filter_author(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_organization_log_record,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    make_organization_log_record(organization, first_user)

    url = reverse("api-internal:organization_log-list")
    first_response = client.get(
        f"{url}?author={first_user.public_primary_key}", format="json", **make_user_auth_headers(first_user, token)
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        f"{url}?author={second_user.public_primary_key}", format="json", **make_user_auth_headers(first_user, token)
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_author_multiple_values(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_organization_log_record,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    third_user = make_user_for_organization(organization)
    make_organization_log_record(organization, first_user)
    make_organization_log_record(organization, second_user)

    url = reverse("api-internal:organization_log-list")
    first_response = client.get(
        f"{url}?author={first_user.public_primary_key}&author={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 2

    second_response = client.get(
        f"{url}?author={first_user.public_primary_key}&author={third_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 1
