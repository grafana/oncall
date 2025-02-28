"""
Tests for the PagerDuty services module.
"""

import unittest
from unittest.mock import MagicMock, patch

from lib.pagerduty.resources.services import (
    TechnicalService,
    fetch_services,
    fetch_service_dependencies,
    get_all_technical_services_with_metadata
)


class TestTechnicalService(unittest.TestCase):
    """Tests for the TechnicalService class."""

    def test_init(self):
        """Test TechnicalService initialization with basic fields."""
        service_data = {
            "id": "SERVICE123",
            "name": "Test Service",
            "description": "A test service",
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "html_url": "https://example.pagerduty.com/service/SERVICE123",
            "self": "https://api.pagerduty.com/services/SERVICE123",
            "escalation_policy": {"id": "EP123", "name": "Test Policy"},
            "teams": [{"id": "TEAM1", "summary": "Team 1"}]
        }

        service = TechnicalService(service_data)

        self.assertEqual(service.id, "SERVICE123")
        self.assertEqual(service.name, "Test Service")
        self.assertEqual(service.description, "A test service")
        self.assertEqual(service.status, "active")
        self.assertEqual(service.created_at, "2023-01-01T00:00:00Z")
        self.assertEqual(service.updated_at, "2023-01-02T00:00:00Z")
        self.assertEqual(service.html_url, "https://example.pagerduty.com/service/SERVICE123")
        self.assertEqual(service.self_url, "https://api.pagerduty.com/services/SERVICE123")
        self.assertEqual(service.escalation_policy, {"id": "EP123", "name": "Test Policy"})
        self.assertEqual(service.teams, [{"id": "TEAM1", "summary": "Team 1"}])
        self.assertEqual(service.dependencies, [])
        self.assertEqual(service.raw_data, service_data)

    def test_str_representation(self):
        """Test string representation of the service."""
        service = TechnicalService({"id": "SERVICE123", "name": "Test Service"})
        self.assertEqual(str(service), "TechnicalService(id=SERVICE123, name=Test Service)")


class TestServiceFunctions(unittest.TestCase):
    """Tests for the service module functions."""

    def test_fetch_services(self):
        """Test fetching services from PagerDuty API."""
        # Mock the API session
        mock_session = MagicMock()
        mock_session.list_all.return_value = [
            {"id": "SERVICE1", "name": "Service 1"},
            {"id": "SERVICE2", "name": "Service 2"}
        ]

        services = fetch_services(mock_session)

        # Verify API call
        mock_session.list_all.assert_called_once_with(
            "services",
            params={"include[]": ["integrations", "teams"]}
        )

        # Verify results
        self.assertEqual(len(services), 2)
        self.assertIsInstance(services[0], TechnicalService)
        self.assertEqual(services[0].id, "SERVICE1")
        self.assertEqual(services[1].id, "SERVICE2")

    def test_fetch_services_without_includes(self):
        """Test fetching services without including integrations or teams."""
        mock_session = MagicMock()
        mock_session.list_all.return_value = [{"id": "SERVICE1"}]

        services = fetch_services(
            mock_session,
            include_integrations=False,
            include_teams=False
        )

        # Verify API call with no includes
        mock_session.list_all.assert_called_once_with("services", params={})

        # Verify results
        self.assertEqual(len(services), 1)
        self.assertIsInstance(services[0], TechnicalService)

    def test_fetch_service_dependencies(self):
        """Test fetching service dependencies."""
        mock_session = MagicMock()
        # Mock the dependencies API call - only mock for the first service to simplify
        mock_session.get.side_effect = [
            {
                "relationships": [
                    {
                        "supporting_service": {
                            "id": "SERVICE2"
                        }
                    }
                ]
            },  # First call returns SERVICE2 as a dependency
            {"relationships": []}  # Second call returns no dependencies
        ]

        # Create services
        service1 = TechnicalService({"id": "SERVICE1", "name": "Service 1"})
        service2 = TechnicalService({"id": "SERVICE2", "name": "Service 2"})
        services = [service1, service2]

        fetch_service_dependencies(mock_session, services)

        # Verify API calls - should be called for each service
        self.assertEqual(mock_session.get.call_count, 2)
        mock_session.get.assert_any_call(
            "service_dependencies/technical_services/SERVICE1"
        )
        mock_session.get.assert_any_call(
            "service_dependencies/technical_services/SERVICE2"
        )

        # Verify that service1 now has service2 as a dependency
        self.assertEqual(len(service1.dependencies), 1)
        self.assertEqual(service1.dependencies[0], service2)
        # Service2 should have no dependencies since the mock returned empty list
        self.assertEqual(len(service2.dependencies), 0)

    @patch("lib.pagerduty.resources.services.fetch_services")
    @patch("lib.pagerduty.resources.services.fetch_service_dependencies")
    def test_get_all_technical_services_with_metadata(self, mock_fetch_deps, mock_fetch_services):
        """Test getting all services with their metadata."""
        mock_session = MagicMock()
        mock_services = [MagicMock(), MagicMock()]
        mock_fetch_services.return_value = mock_services

        result = get_all_technical_services_with_metadata(mock_session)

        # Verify calls
        mock_fetch_services.assert_called_once_with(mock_session)
        mock_fetch_deps.assert_called_once_with(mock_session, mock_services)

        # Verify result
        self.assertEqual(result, mock_services)


if __name__ == "__main__":
    unittest.main()