import os
import uuid
from unittest.mock import patch

import pytest

from lib.session import SESSION_FILE, get_or_create_session_id


@pytest.fixture
def cleanup_session_file():
    # Clean up before test
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

    yield

    # Clean up after test
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


def test_get_or_create_session_id_creates_new(cleanup_session_file):
    # First call should create a new session ID
    session_id1 = get_or_create_session_id()
    assert session_id1 is not None
    assert len(session_id1) > 0

    # Verify it's a valid UUID
    uuid.UUID(session_id1)

    # Second call should return the same ID
    session_id2 = get_or_create_session_id()
    assert session_id2 == session_id1

    # Verify file exists and contains the ID
    assert os.path.exists(SESSION_FILE)
    with open(SESSION_FILE, "r") as f:
        stored_id = f.read().strip()
    assert stored_id == session_id1


@patch("uuid.uuid4")
def test_get_or_create_session_id_uses_existing(mock_uuid, cleanup_session_file):
    # Create a session file with a known ID
    test_id = "12345678-1234-5678-1234-567812345678"
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        f.write(test_id)

    # Should return existing ID without generating new one
    session_id = get_or_create_session_id()
    assert session_id == test_id
    mock_uuid.assert_not_called()
