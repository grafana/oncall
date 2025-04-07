from unittest.mock import patch

import pytest

from lib.pagerduty.resources.users import filter_users


@pytest.fixture
def users():
    return [
        {"id": "USER1", "name": "User 1"},
        {"id": "USER2", "name": "User 2"},
        {"id": "USER3", "name": "User 3"},
    ]


@patch("lib.pagerduty.resources.users.PAGERDUTY_FILTER_USERS", ["USER1", "USER3"])
def test_filter_users(users):
    """Test filtering users by ID when PAGERDUTY_FILTER_USERS is set."""
    filtered = filter_users(users)
    assert len(filtered) == 2
    assert {u["id"] for u in filtered} == {"USER1", "USER3"}


@patch("lib.pagerduty.resources.users.PAGERDUTY_FILTER_USERS", [])
def test_filter_users_no_filter(users):
    """Test that all users are kept when PAGERDUTY_FILTER_USERS is empty."""
    filtered = filter_users(users)
    assert len(filtered) == 3
    assert {u["id"] for u in filtered} == {"USER1", "USER2", "USER3"}
