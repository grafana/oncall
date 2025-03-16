"""
Tests for the PagerDuty services module.
"""

from unittest.mock import MagicMock, patch

import pytest

from lib.pagerduty.resources.services import (
    TechnicalService,
    fetch_service_dependencies,
    fetch_services,
    get_all_technical_services_with_metadata,
)


@pytest.fixture
def service_data():
    """Basic service data fixture."""
    return {
        "id": "SERVICE123",
        "name": "Test Service",
        "description": "A test service",
        "status": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "html_url": "https://example.pagerduty.com/service/SERVICE123",
        "self": "https://api.pagerduty.com/services/SERVICE123",
        "escalation_policy": {"id": "EP123", "name": "Test Policy"},
        "teams": [{"id": "TEAM1", "summary": "Team 1"}],
    }


def test_technical_service_init(service_data):
    """Test TechnicalService initialization with basic fields."""
    service = TechnicalService(service_data)

    assert service.id == "SERVICE123"
    assert service.name == "Test Service"
    assert service.description == "A test service"
    assert service.status == "active"
    assert service.created_at == "2023-01-01T00:00:00Z"
    assert service.updated_at == "2023-01-02T00:00:00Z"
    assert service.html_url == "https://example.pagerduty.com/service/SERVICE123"
    assert service.self_url == "https://api.pagerduty.com/services/SERVICE123"
    assert service.escalation_policy == {"id": "EP123", "name": "Test Policy"}
    assert service.teams == [{"id": "TEAM1", "summary": "Team 1"}]
    assert service.dependencies == []
    assert service.raw_data == service_data


def test_technical_service_str():
    """Test string representation of the service."""
    service = TechnicalService({"id": "SERVICE123", "name": "Test Service"})
    assert str(service) == "TechnicalService(id=SERVICE123, name=Test Service)"


@pytest.fixture
def mock_session():
    """Create a mock API session."""
    return MagicMock()


def test_fetch_services(mock_session):
    """Test fetching services from PagerDuty API."""
    mock_session.list_all.return_value = [
        {"id": "SERVICE1", "name": "Service 1"},
        {"id": "SERVICE2", "name": "Service 2"},
    ]

    services = fetch_services(mock_session)

    # Verify API call
    mock_session.list_all.assert_called_once_with(
        "services", params={"include[]": ["integrations", "teams"]}
    )

    # Verify results
    assert len(services) == 2
    assert isinstance(services[0], TechnicalService)
    assert services[0].id == "SERVICE1"
    assert services[1].id == "SERVICE2"


def test_fetch_services_without_includes(mock_session):
    """Test fetching services without including integrations or teams."""
    mock_session.list_all.return_value = [{"id": "SERVICE1"}]

    services = fetch_services(
        mock_session, include_integrations=False, include_teams=False
    )

    # Verify API call with no includes
    mock_session.list_all.assert_called_once_with("services", params={})

    # Verify results
    assert len(services) == 1
    assert isinstance(services[0], TechnicalService)


@pytest.fixture
def mock_services():
    """Create mock services for dependency testing."""
    service1 = TechnicalService({"id": "SERVICE1", "name": "Service 1"})
    service2 = TechnicalService({"id": "SERVICE2", "name": "Service 2"})
    return [service1, service2]


def test_fetch_service_dependencies(mock_session, mock_services):
    """Test fetching service dependencies."""
    # Mock the dependencies API call - only mock for the first service to simplify
    mock_session.get.side_effect = [
        {
            "relationships": [{"supporting_service": {"id": "SERVICE2"}}]
        },  # First call returns SERVICE2 as a dependency
        {"relationships": []},  # Second call returns no dependencies
    ]

    fetch_service_dependencies(mock_session, mock_services)

    # Verify API calls - should be called for each service
    assert mock_session.get.call_count == 2
    mock_session.get.assert_any_call("service_dependencies/technical_services/SERVICE1")
    mock_session.get.assert_any_call("service_dependencies/technical_services/SERVICE2")

    # Verify that service1 now has service2 as a dependency
    assert len(mock_services[0].dependencies) == 1
    assert mock_services[0].dependencies[0] == mock_services[1]
    # Service2 should have no dependencies since the mock returned empty list
    assert len(mock_services[1].dependencies) == 0


def test_get_all_technical_services_with_metadata():
    """Test getting all services with their metadata."""
    mock_session = MagicMock()
    mock_services = [MagicMock(), MagicMock()]

    with patch(
        "lib.pagerduty.resources.services.fetch_services"
    ) as mock_fetch_services:
        with patch(
            "lib.pagerduty.resources.services.fetch_service_dependencies"
        ) as mock_fetch_deps:
            mock_fetch_services.return_value = mock_services

            result = get_all_technical_services_with_metadata(mock_session)

            # Verify calls
            mock_fetch_services.assert_called_once_with(mock_session)
            mock_fetch_deps.assert_called_once_with(mock_session, mock_services)

            # Verify result
            assert result == mock_services
