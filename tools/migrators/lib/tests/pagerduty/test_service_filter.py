"""
Tests for service filtering functionality.
"""

import pytest
from unittest.mock import patch

from lib.common.resources.services import filter_services
from lib.pagerduty.config import (
    PAGERDUTY_FILTER_TEAM,
    PAGERDUTY_FILTER_USERS,
    PAGERDUTY_FILTER_SERVICE_REGEX,
)


@pytest.fixture
def sample_services():
    """Sample service data for testing."""
    return [
        {
            "id": "P123",
            "name": "Production Service",
            "type": "service",
            "teams": [{"summary": "Platform Team"}],
            "escalation_policy": {
                "escalation_rules": [
                    {
                        "targets": [
                            {"type": "user", "id": "U123"},
                            {"type": "user", "id": "U456"}
                        ]
                    }
                ]
            }
        },
        {
            "id": "P456",
            "name": "Staging Service",
            "type": "service",
            "teams": [{"summary": "DevOps Team"}],
            "escalation_policy": {
                "escalation_rules": [
                    {
                        "targets": [
                            {"type": "user", "id": "U789"}
                        ]
                    }
                ]
            }
        },
        {
            "id": "B123",
            "name": "Business Service",
            "type": "business_service",
            "teams": [{"summary": "Platform Team"}]
        }
    ]


def test_filter_services_by_team(sample_services):
    """Test filtering services by team."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_TEAM", "Platform Team"):
        filtered = filter_services(sample_services)
        assert len(filtered) == 2
        assert all(service["teams"][0]["summary"] == "Platform Team" for service in filtered)


def test_filter_services_by_users(sample_services):
    """Test filtering services by users in escalation policy."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_USERS", ["U123"]):
        filtered = filter_services(sample_services)
        # Should include both the matching technical service and the business service
        assert len(filtered) == 2
        # Verify the technical service with matching user is included
        assert any(service["id"] == "P123" for service in filtered)
        # Verify the business service is included (not filtered by users)
        assert any(service["type"] == "business_service" for service in filtered)


def test_filter_services_by_regex(sample_services):
    """Test filtering services by name regex pattern."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_SERVICE_REGEX", "Prod.*"):
        filtered = filter_services(sample_services)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Production Service"


def test_filter_services_no_filters(sample_services):
    """Test that no filters returns all services."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_TEAM", ""), \
         patch("lib.common.resources.services.PAGERDUTY_FILTER_USERS", []), \
         patch("lib.common.resources.services.PAGERDUTY_FILTER_SERVICE_REGEX", ""):
        filtered = filter_services(sample_services)
        assert len(filtered) == len(sample_services)


def test_filter_services_multiple_filters(sample_services):
    """Test applying multiple filters together."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_TEAM", "Platform Team"), \
         patch("lib.common.resources.services.PAGERDUTY_FILTER_USERS", ["U123"]), \
         patch("lib.common.resources.services.PAGERDUTY_FILTER_SERVICE_REGEX", "Prod.*"):
        filtered = filter_services(sample_services)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "P123"
        assert filtered[0]["teams"][0]["summary"] == "Platform Team"
        assert filtered[0]["name"] == "Production Service"


def test_filter_services_business_services(sample_services):
    """Test that business services are not filtered by user assignments."""
    with patch("lib.common.resources.services.PAGERDUTY_FILTER_USERS", ["U123"]):
        filtered = filter_services(sample_services)
        assert len(filtered) == 2
        assert any(service["type"] == "business_service" for service in filtered)