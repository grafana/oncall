import os
import uuid
from pathlib import Path

# Use environment variable for session file location, with fallback
SESSION_FILE = Path(
    os.environ.get("SESSION_FILE", str(Path(__file__).parent.parent / ".session"))
)


def get_or_create_session_id() -> str:
    """Get an existing session ID or create a new one if it doesn't exist."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return f.read().strip()

    # Create new session ID
    session_id = str(uuid.uuid4())

    # Ensure directory exists
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save session ID
    with open(SESSION_FILE, "w") as f:
        f.write(session_id)

    return session_id
