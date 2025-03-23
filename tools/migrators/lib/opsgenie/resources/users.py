from lib.opsgenie.config import OPSGENIE_FILTER_TEAM, OPSGENIE_FILTER_USERS


def filter_users(users: list[dict]) -> list[dict]:
    """Apply filters to users."""
    if OPSGENIE_FILTER_TEAM:
        filtered_users = []
        for u in users:
            if any(t["id"] == OPSGENIE_FILTER_TEAM for t in u["teams"]):
                filtered_users.append(u)
        users = filtered_users

    if OPSGENIE_FILTER_USERS:
        users = [u for u in users if u["id"] in OPSGENIE_FILTER_USERS]

    return users
