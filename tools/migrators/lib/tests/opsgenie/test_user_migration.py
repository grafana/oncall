import pytest
from unittest.mock import patch, MagicMock

from add_users_to_grafana import migrate_opsgenie_users, create_grafana_user


@patch('lib.opsgenie.api_client.OpsGenieAPIClient')
@patch('lib.grafana.api_client.GrafanaAPIClient')
def test_migrate_opsgenie_users(mock_grafana_client, mock_opsgenie_client):
    # Mock OpsGenie users
    mock_opsgenie_client.return_value.fetch_users.return_value = [
        {
            "fullName": "John Doe",
            "username": "john.doe@example.com",
        },
        {
            "fullName": "Jane Smith",
            "username": "jane.smith@example.com",
        },
    ]

    # Mock Grafana API responses
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response2 = MagicMock()
    mock_response2.status_code = 412  # User already exists

    mock_grafana_client.return_value.create_user_with_random_password.side_effect = [
        mock_response1,
        mock_response2,
    ]

    # Run migration
    migrate_opsgenie_users()

    # Verify OpsGenie API calls
    mock_opsgenie_client.return_value.fetch_users.assert_called_once()

    # Verify Grafana API calls
    mock_grafana_client.return_value.create_user_with_random_password.assert_any_call(
        "John Doe", "john.doe@example.com"
    )
    mock_grafana_client.return_value.create_user_with_random_password.assert_any_call(
        "Jane Smith", "jane.smith@example.com"
    )


@patch('lib.grafana.api_client.GrafanaAPIClient')
def test_create_grafana_user_success(mock_grafana_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_grafana_client.return_value.create_user_with_random_password.return_value = mock_response

    create_grafana_user("John Doe", "john.doe@example.com")
    mock_grafana_client.return_value.create_user_with_random_password.assert_called_once_with(
        "John Doe", "john.doe@example.com"
    )


@patch('lib.grafana.api_client.GrafanaAPIClient')
def test_create_grafana_user_already_exists(mock_grafana_client):
    mock_response = MagicMock()
    mock_response.status_code = 412
    mock_grafana_client.return_value.create_user_with_random_password.return_value = mock_response

    create_grafana_user("John Doe", "john.doe@example.com")
    mock_grafana_client.return_value.create_user_with_random_password.assert_called_once_with(
        "John Doe", "john.doe@example.com"
    )


@patch('lib.grafana.api_client.GrafanaAPIClient')
def test_create_grafana_user_unauthorized(mock_grafana_client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_grafana_client.return_value.create_user_with_random_password.return_value = mock_response

    with pytest.raises(SystemExit):
        create_grafana_user("John Doe", "john.doe@example.com")
