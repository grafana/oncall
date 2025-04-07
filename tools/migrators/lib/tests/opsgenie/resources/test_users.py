from unittest.mock import patch

from lib.opsgenie.resources.users import filter_users


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", None)
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", None)
def test_filter_users_no_filters():
    """Test that filter_users returns all users when no filters are set."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}, {"id": "t2"}]},
        {"id": "u2", "teams": [{"id": "t3"}]},
    ]
    filtered = filter_users(users)
    assert filtered == users


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", None)
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", "t1")
def test_filter_users_by_team():
    """Test filtering users by team ID."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}, {"id": "t2"}]},
        {"id": "u2", "teams": [{"id": "t3"}]},
        {"id": "u3", "teams": [{"id": "t1"}, {"id": "t3"}]},
    ]
    filtered = filter_users(users)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "u1"
    assert filtered[1]["id"] == "u3"


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", ["u1", "u3"])
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", None)
def test_filter_users_by_user_ids():
    """Test filtering users by specific user IDs."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}]},
        {"id": "u2", "teams": [{"id": "t2"}]},
        {"id": "u3", "teams": [{"id": "t3"}]},
    ]
    filtered = filter_users(users)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "u1"
    assert filtered[1]["id"] == "u3"


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", ["u1", "u4"])
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", "t1")
def test_filter_users_by_team_and_user_ids():
    """Test filtering users by both team ID and user IDs."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}]},  # Matches both filters
        {"id": "u2", "teams": [{"id": "t1"}]},  # Matches team only
        {"id": "u3", "teams": [{"id": "t2"}]},  # Matches neither
        {"id": "u4", "teams": [{"id": "t2"}]},  # Matches user ID only
    ]
    filtered = filter_users(users)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "u1"  # Only user matching both filters


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", ["u1"])
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", "t1")
def test_filter_users_empty_list():
    """Test filtering an empty user list."""
    filtered = filter_users([])
    assert filtered == []


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", None)
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", "t3")
def test_filter_users_no_matching_team():
    """Test filtering when no users match the team filter."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}]},
        {"id": "u2", "teams": [{"id": "t2"}]},
    ]
    filtered = filter_users(users)
    assert filtered == []


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", ["u3", "u4"])
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", None)
def test_filter_users_no_matching_user_ids():
    """Test filtering when no users match the user ID filter."""
    users = [
        {"id": "u1", "teams": [{"id": "t1"}]},
        {"id": "u2", "teams": [{"id": "t2"}]},
    ]
    filtered = filter_users(users)
    assert filtered == []


@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_USERS", None)
@patch("lib.opsgenie.resources.users.OPSGENIE_FILTER_TEAM", "t1")
def test_filter_users_with_empty_teams():
    """Test filtering users that have no teams."""
    users = [
        {"id": "u1", "teams": []},
        {"id": "u2", "teams": [{"id": "t1"}]},
    ]
    filtered = filter_users(users)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "u2"
