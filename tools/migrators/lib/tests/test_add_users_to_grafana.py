from unittest.mock import call, patch


class MockResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self.json_data = json_data or {}
        self.text = ""

    def json(self):
        return self.json_data


@patch("pdpyras.APISession")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "pagerduty",
        "PAGERDUTY_API_TOKEN": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
        "PAGERDUTY_FILTER_USERS": "",
    },
)
def test_migrate_all_pagerduty_users(
    mock_exit, mock_grafana_client_class, mock_api_session_class
):
    mock_session_instance = mock_api_session_class.return_value
    mock_session_instance.list_all.return_value = [
        {"id": "USER1", "name": "User One", "email": "user1@example.com"},
        {"id": "USER2", "name": "User Two", "email": "user2@example.com"},
        {"id": "USER3", "name": "User Three", "email": "user3@example.com"},
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        200
    )

    # Now import the module and call the function
    # Force reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_pagerduty_users()

    assert mock_session_instance.list_all.call_args == call("users")
    assert mock_grafana_instance.create_user_with_random_password.call_count == 3
    mock_exit.assert_not_called()

    # Verify all 3 users were processed
    calls = mock_grafana_instance.create_user_with_random_password.call_args_list
    call_emails = [call[0][1] for call in calls]
    assert "user1@example.com" in call_emails
    assert "user2@example.com" in call_emails
    assert "user3@example.com" in call_emails


@patch("pdpyras.APISession")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "pagerduty",
        "PAGERDUTY_API_TOKEN": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
        "PAGERDUTY_FILTER_USERS": "USER1,USER3",
    },
)
def test_migrate_filtered_pagerduty_users(
    mock_exit, mock_grafana_client_class, mock_api_session_class
):
    mock_session_instance = mock_api_session_class.return_value
    mock_session_instance.list_all.return_value = [
        {"id": "USER1", "name": "User One", "email": "user1@example.com"},
        {"id": "USER2", "name": "User Two", "email": "user2@example.com"},
        {"id": "USER3", "name": "User Three", "email": "user3@example.com"},
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        200
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_pagerduty_users()

    assert mock_session_instance.list_all.call_args == call("users")
    assert mock_grafana_instance.create_user_with_random_password.call_count == 2
    mock_exit.assert_not_called()

    # Verify only USER1 and USER3 were processed
    calls = mock_grafana_instance.create_user_with_random_password.call_args_list
    call_emails = [call[0][1] for call in calls]
    assert "user1@example.com" in call_emails
    assert "user3@example.com" in call_emails
    assert "user2@example.com" not in call_emails


@patch("pdpyras.APISession")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "pagerduty",
        "PAGERDUTY_API_TOKEN": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_pagerduty_error_handling(
    mock_exit, mock_grafana_client_class, mock_api_session_class
):
    mock_session_instance = mock_api_session_class.return_value
    mock_session_instance.list_all.return_value = [
        {"id": "USER1", "name": "User One", "email": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        401
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_pagerduty_users()

    # Verify sys.exit was called with the correct error message
    mock_exit.assert_called_once()
    call_args = mock_exit.call_args[0][0]
    assert "Invalid username or password" in call_args


@patch("pdpyras.APISession")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch("builtins.print")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "pagerduty",
        "PAGERDUTY_API_TOKEN": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_pagerduty_user_already_exists(
    mock_print, mock_exit, mock_grafana_client_class, mock_api_session_class
):
    mock_session_instance = mock_api_session_class.return_value
    mock_session_instance.list_all.return_value = [
        {"id": "USER1", "name": "User One", "email": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        412
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_pagerduty_users()

    already_exists_message_found = False
    for call_args in mock_print.call_args_list:
        if (
            len(call_args[0]) > 0
            and isinstance(call_args[0][0], str)
            and "already exists" in call_args[0][0]
        ):
            already_exists_message_found = True
            break

    assert (
        already_exists_message_found
    ), 'Expected "already exists" message not found in print calls'
    # Verify sys.exit was not called
    mock_exit.assert_not_called()


@patch("lib.splunk.api_client.SplunkOnCallAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "splunk",
        "SPLUNK_API_ID": "test_id",
        "SPLUNK_API_KEY": "test_key",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_migrate_all_splunk_users(
    mock_exit, mock_grafana_client_class, mock_splunk_client_class
):
    mock_splunk_instance = mock_splunk_client_class.return_value
    mock_splunk_instance.fetch_users.return_value = [
        {"firstName": "User", "lastName": "One", "email": "user1@example.com"},
        {"firstName": "User", "lastName": "Two", "email": "user2@example.com"},
        {"firstName": "User", "lastName": "Three", "email": "user3@example.com"},
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        200
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_splunk_users()

    assert mock_splunk_instance.fetch_users.call_args == call(
        include_paging_policies=False
    )
    assert mock_grafana_instance.create_user_with_random_password.call_count == 3
    mock_exit.assert_not_called()

    # Verify all 3 users were processed
    calls = mock_grafana_instance.create_user_with_random_password.call_args_list
    call_emails = [call[0][1] for call in calls]
    assert "user1@example.com" in call_emails
    assert "user2@example.com" in call_emails
    assert "user3@example.com" in call_emails


@patch("lib.splunk.api_client.SplunkOnCallAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "splunk",
        "SPLUNK_API_ID": "test_id",
        "SPLUNK_API_KEY": "test_key",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_splunk_error_handling(
    mock_exit, mock_grafana_client_class, mock_splunk_client_class
):
    # Setup mocks
    mock_splunk_instance = mock_splunk_client_class.return_value
    mock_splunk_instance.fetch_users.return_value = [
        {"firstName": "User", "lastName": "One", "email": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        401
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_splunk_users()

    # Verify sys.exit was called with the correct error message
    mock_exit.assert_called_once()
    call_args = mock_exit.call_args[0][0]
    assert "Invalid username or password" in call_args


@patch("lib.splunk.api_client.SplunkOnCallAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch("builtins.print")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "splunk",
        "SPLUNK_API_ID": "test_id",
        "SPLUNK_API_KEY": "test_key",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_splunk_user_already_exists(
    mock_print, mock_exit, mock_grafana_client_class, mock_splunk_client_class
):
    mock_splunk_instance = mock_splunk_client_class.return_value
    mock_splunk_instance.fetch_users.return_value = [
        {"firstName": "User", "lastName": "One", "email": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        412
    )

    # Import the module and reload to ensure our mocks are used
    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_splunk_users()

    already_exists_message_found = False
    for call_args in mock_print.call_args_list:
        if (
            len(call_args[0]) > 0
            and isinstance(call_args[0][0], str)
            and "already exists" in call_args[0][0]
        ):
            already_exists_message_found = True
            break

    assert (
        already_exists_message_found
    ), 'Expected "already exists" message not found in print calls'
    # Verify sys.exit was not called
    mock_exit.assert_not_called()


@patch("lib.opsgenie.api_client.OpsGenieAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "opsgenie",
        "OPSGENIE_API_KEY": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
        "OPSGENIE_FILTER_USERS": "",
    },
)
def test_migrate_all_opsgenie_users(
    mock_exit, mock_grafana_client_class, mock_opsgenie_client_class
):
    mock_opsgenie_instance = mock_opsgenie_client_class.return_value
    mock_opsgenie_instance.list_users.return_value = [
        {"id": "USER1", "fullName": "User One", "username": "user1@example.com"},
        {"id": "USER2", "fullName": "User Two", "username": "user2@example.com"},
        {"id": "USER3", "fullName": "User Three", "username": "user3@example.com"},
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        200
    )

    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_opsgenie_users()

    assert mock_opsgenie_instance.list_users.called
    assert mock_grafana_instance.create_user_with_random_password.call_count == 3
    mock_exit.assert_not_called()

    calls = mock_grafana_instance.create_user_with_random_password.call_args_list
    call_emails = [call[0][1] for call in calls]
    assert "user1@example.com" in call_emails
    assert "user2@example.com" in call_emails
    assert "user3@example.com" in call_emails


@patch("lib.opsgenie.api_client.OpsGenieAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "opsgenie",
        "OPSGENIE_API_KEY": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
        "OPSGENIE_FILTER_USERS": "USER1,USER3",
    },
)
def test_migrate_filtered_opsgenie_users(
    mock_exit, mock_grafana_client_class, mock_opsgenie_client_class
):
    mock_opsgenie_instance = mock_opsgenie_client_class.return_value
    mock_opsgenie_instance.list_users.return_value = [
        {"id": "USER1", "fullName": "User One", "username": "user1@example.com"},
        {"id": "USER2", "fullName": "User Two", "username": "user2@example.com"},
        {"id": "USER3", "fullName": "User Three", "username": "user3@example.com"},
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        200
    )

    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_opsgenie_users()

    assert mock_opsgenie_instance.list_users.called
    assert mock_grafana_instance.create_user_with_random_password.call_count == 2
    mock_exit.assert_not_called()

    calls = mock_grafana_instance.create_user_with_random_password.call_args_list
    call_emails = [call[0][1] for call in calls]
    assert "user1@example.com" in call_emails
    assert "user3@example.com" in call_emails
    assert "user2@example.com" not in call_emails


@patch("lib.opsgenie.api_client.OpsGenieAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "opsgenie",
        "OPSGENIE_API_KEY": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_opsgenie_error_handling(
    mock_exit, mock_grafana_client_class, mock_opsgenie_client_class
):
    mock_opsgenie_instance = mock_opsgenie_client_class.return_value
    mock_opsgenie_instance.list_users.return_value = [
        {"id": "USER1", "fullName": "User One", "username": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        401
    )

    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_opsgenie_users()

    mock_exit.assert_called_once()
    call_args = mock_exit.call_args[0][0]
    assert "Invalid username or password" in call_args


@patch("lib.opsgenie.api_client.OpsGenieAPIClient")
@patch("lib.grafana.api_client.GrafanaAPIClient")
@patch("sys.exit")
@patch("builtins.print")
@patch.dict(
    "os.environ",
    {
        "MIGRATING_FROM": "opsgenie",
        "OPSGENIE_API_KEY": "test_token",
        "GRAFANA_URL": "http://test.com",
        "GRAFANA_USERNAME": "test_user",
        "GRAFANA_PASSWORD": "test_pass",
    },
)
def test_opsgenie_user_already_exists(
    mock_print, mock_exit, mock_grafana_client_class, mock_opsgenie_client_class
):
    mock_opsgenie_instance = mock_opsgenie_client_class.return_value
    mock_opsgenie_instance.list_users.return_value = [
        {"id": "USER1", "fullName": "User One", "username": "user1@example.com"}
    ]

    mock_grafana_instance = mock_grafana_client_class.return_value
    mock_grafana_instance.create_user_with_random_password.return_value = MockResponse(
        412
    )

    import importlib

    import add_users_to_grafana

    importlib.reload(add_users_to_grafana)

    add_users_to_grafana.migrate_opsgenie_users()

    already_exists_message_found = False
    for call_args in mock_print.call_args_list:
        if (
            len(call_args[0]) > 0
            and isinstance(call_args[0][0], str)
            and "already exists" in call_args[0][0]
        ):
            already_exists_message_found = True
            break

    assert (
        already_exists_message_found
    ), 'Expected "already exists" message not found in print calls'
    mock_exit.assert_not_called()
