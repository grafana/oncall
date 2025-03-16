"""
Common service filtering functionality.
"""

import re
from typing import Any, Dict, List

from lib.pagerduty.config import (
    PAGERDUTY_FILTER_SERVICE_REGEX,
    PAGERDUTY_FILTER_TEAM,
    PAGERDUTY_FILTER_USERS,
)


def filter_services(
    services: List[Dict[str, Any]], tab: str = ""
) -> List[Dict[str, Any]]:
    """
    Filter services based on configured filters.

    Args:
        services: List of service dictionaries to filter
        tab: Optional indentation prefix for logging

    Returns:
        List of filtered services
    """
    filtered_services = []
    filtered_out = 0

    for service in services:
        should_include = True
        reason = None

        # Filter by team
        if PAGERDUTY_FILTER_TEAM:
            teams = service.get("teams", [])
            if not any(team["summary"] == PAGERDUTY_FILTER_TEAM for team in teams):
                should_include = False
                reason = f"No teams found for team filter: {PAGERDUTY_FILTER_TEAM}"

        # Filter by users (for technical services)
        if (
            should_include
            and PAGERDUTY_FILTER_USERS
            and service.get("type") != "business_service"
        ):
            service_users = set()
            # Get users from escalation policy if present
            if service.get("escalation_policy"):
                for rule in service["escalation_policy"].get("escalation_rules", []):
                    for target in rule.get("targets", []):
                        if target["type"] == "user":
                            service_users.add(target["id"])

            if not any(user_id in service_users for user_id in PAGERDUTY_FILTER_USERS):
                should_include = False
                reason = f"No users found for user filter: {','.join(PAGERDUTY_FILTER_USERS)}"

        # Filter by name regex
        if should_include and PAGERDUTY_FILTER_SERVICE_REGEX:
            if not re.match(PAGERDUTY_FILTER_SERVICE_REGEX, service["name"]):
                should_include = False
                reason = f"Service name does not match regex: {PAGERDUTY_FILTER_SERVICE_REGEX}"

        if should_include:
            filtered_services.append(service)
        else:
            filtered_out += 1
            print(f"{tab}Service {service['id']}: {reason}")

    if filtered_out > 0:
        print(f"Filtered out {filtered_out} services")

    return filtered_services
