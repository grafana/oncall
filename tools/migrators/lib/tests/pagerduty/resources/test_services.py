from unittest.mock import MagicMock, Mock, patch

import pytest

from lib.pagerduty.resources.services import (
    BusinessService,
    TechnicalService,
    _transform_service,
    _validate_component,
    fetch_service_dependencies,
    fetch_services,
    filter_services,
    get_all_technical_services_with_metadata,
)


@pytest.fixture
def mock_session():
    """Create a mock API session."""
    return MagicMock()


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
                            {"type": "user_reference", "id": "U123"},
                            {"type": "user_reference", "id": "U456"},
                        ]
                    }
                ]
            },
        },
        {
            "id": "P456",
            "name": "Staging Service",
            "type": "service",
            "teams": [{"summary": "DevOps Team"}],
            "escalation_policy": {
                "escalation_rules": [
                    {"targets": [{"type": "user_reference", "id": "U789"}]}
                ]
            },
        },
        {
            "id": "B123",
            "name": "Business Service",
            "type": "business_service",
            "teams": [{"summary": "Platform Team"}],
        },
    ]


@pytest.fixture
def mock_services():
    """Create mock services for dependency testing."""
    service1 = TechnicalService({"id": "SERVICE1", "name": "Service 1"})
    service2 = TechnicalService({"id": "SERVICE2", "name": "Service 2"})
    return [service1, service2]


@pytest.fixture
def technical_service():
    """Create a mock technical service for testing."""
    service = Mock(spec=TechnicalService)
    service.name = "Test Service"
    service.description = "A test service"
    service.id = "P123456"
    service.status = "active"
    service.html_url = "https://pagerduty.com/services/P123456"
    service.self_url = "https://api.pagerduty.com/services/P123456"
    return service


@pytest.fixture
def business_service():
    """Create a mock business service for testing."""
    service = Mock(spec=BusinessService)
    service.name = "Test Business Service"
    service.description = "A test business service"
    service.id = "P789012"
    service.html_url = "https://pagerduty.com/services/P789012"
    service.self_url = "https://api.pagerduty.com/services/P789012"
    return service


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_TEAM", "Platform Team")
def test_filter_services_by_team(sample_services):
    """Test filtering services by team."""
    filtered = filter_services(sample_services)
    assert len(filtered) == 2
    assert all(
        service["teams"][0]["summary"] == "Platform Team" for service in filtered
    )


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_USERS", ["U123"])
def test_filter_services_by_users(sample_services):
    """Test filtering services by users in escalation policy."""
    filtered = filter_services(sample_services)
    # Should include both the matching technical service and the business service
    assert len(filtered) == 2
    # Verify the technical service with matching user is included
    assert any(service["id"] == "P123" for service in filtered)
    # Verify the business service is included (not filtered by users)
    assert any(service["type"] == "business_service" for service in filtered)


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_SERVICE_REGEX", "Prod.*")
def test_filter_services_by_regex(sample_services):
    """Test filtering services by name regex pattern."""
    filtered = filter_services(sample_services)
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Production Service"


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_TEAM", "")
@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_USERS", [])
def test_filter_services_no_filters(sample_services):
    """Test that no filters returns all services."""
    filtered = filter_services(sample_services)
    assert len(filtered) == len(sample_services)


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_TEAM", "Platform Team")
@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_USERS", ["U123"])
@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_SERVICE_REGEX", "Prod.*")
def test_filter_services_multiple_filters(sample_services):
    """Test applying multiple filters together."""
    filtered = filter_services(sample_services)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "P123"
    assert filtered[0]["teams"][0]["summary"] == "Platform Team"
    assert filtered[0]["name"] == "Production Service"


@patch("lib.pagerduty.resources.services.PAGERDUTY_FILTER_USERS", ["U123"])
def test_filter_services_business_services(sample_services):
    """Test that business services are not filtered by user assignments."""
    filtered = filter_services(sample_services)
    assert len(filtered) == 2
    assert any(service["type"] == "business_service" for service in filtered)


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


def test_fetch_services(mock_session):
    """Test fetching services from PagerDuty API."""
    mock_session.list_all.return_value = [
        {"id": "SERVICE1", "name": "Service 1"},
        {"id": "SERVICE2", "name": "Service 2"},
    ]

    services = fetch_services(mock_session)

    # Verify API call
    mock_session.list_all.assert_called_once_with(
        "services",
        params={"include[]": ["integrations", "teams", "escalation_policies"]},
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
    mock_session.list_all.assert_called_once_with(
        "services", params={"include[]": ["escalation_policies"]}
    )

    # Verify results
    assert len(services) == 1
    assert isinstance(services[0], TechnicalService)


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


@patch("lib.pagerduty.resources.services.fetch_service_dependencies")
@patch("lib.pagerduty.resources.services.fetch_services")
def test_get_all_technical_services_with_metadata(mock_fetch_services, mock_fetch_deps):
    """Test getting all services with their metadata."""
    mock_session = MagicMock()
    mock_services = [MagicMock(), MagicMock()]

    mock_fetch_services.return_value = mock_services

    result = get_all_technical_services_with_metadata(mock_session)

    # Verify calls
    mock_fetch_services.assert_called_once_with(mock_session)
    mock_fetch_deps.assert_called_once_with(mock_session, mock_services)

    # Verify result
    assert result == mock_services


def test_transform_technical_service(technical_service):
    """Test transforming a technical service."""
    component = _transform_service(technical_service)

    # Verify the component structure
    assert component["apiVersion"] == "servicemodel.ext.grafana.com/v1alpha1"
    assert component["kind"] == "Component"
    assert component["metadata"]["name"] == "test-service"
    assert component["spec"]["type"] == "service"
    assert component["spec"]["description"] == "A test service"

    # Verify annotations
    annotations = component["metadata"]["annotations"]
    assert annotations["pagerduty.com/service-id"] == "P123456"
    assert annotations["pagerduty.com/status"] == "active"
    assert (
        annotations["pagerduty.com/html-url"]
        == "https://pagerduty.com/services/P123456"
    )
    assert (
        annotations["pagerduty.com/api-url"]
        == "https://api.pagerduty.com/services/P123456"
    )


def test_transform_business_service(business_service):
    """Test transforming a business service."""
    component = _transform_service(business_service)

    # Verify the component structure
    assert component["apiVersion"] == "servicemodel.ext.grafana.com/v1alpha1"
    assert component["kind"] == "Component"
    assert component["metadata"]["name"] == "test-business-service"
    assert component["spec"]["type"] == "business_service"
    assert component["spec"]["description"] == "A test business service"

    # Verify annotations
    annotations = component["metadata"]["annotations"]
    assert annotations["pagerduty.com/service-id"] == "P789012"
    assert (
        annotations["pagerduty.com/html-url"]
        == "https://pagerduty.com/services/P789012"
    )
    assert (
        annotations["pagerduty.com/api-url"]
        == "https://api.pagerduty.com/services/P789012"
    )


@pytest.mark.parametrize(
    "input_name,expected_name",
    [
        # Basic cases
        ("Simple Service", "simple-service"),
        ("Test_Service", "test-service"),
        ("Service.Name", "service.name"),
        # Edge cases that would cause issues with old logic
        ("  Leading spaces", "leading-spaces"),
        ("Trailing spaces  ", "trailing-spaces"),
        ("  Both sides  ", "both-sides"),
        ("Multiple   spaces", "multiple-spaces"),
        # Special characters
        ("Service@Name", "service-name"),
        ("Service!@#$%Name", "service-name"),
        ("Service(with)parens", "service-with-parens"),
        # Mixed cases
        ("  Service@Name  ", "service-name"),
        ("##Service Name##", "service-name"),
        ("!!!Service!!!Name!!!", "service-name"),
    ],
)
def test_service_name_normalization(input_name, expected_name):
    """Test service name normalization handles various edge cases correctly."""
    # Create a mock technical service
    service = Mock(spec=TechnicalService)
    service.name = input_name
    service.description = "Test description"
    service.id = "P123456"
    service.status = "active"
    service.html_url = "https://pagerduty.com/services/P123456"
    service.self_url = "https://api.pagerduty.com/services/P123456"

    # Transform the service
    component = _transform_service(service)

    # Check that the name was normalized correctly
    assert (
        component["metadata"]["name"] == expected_name
    ), f"Expected '{expected_name}' for input '{input_name}', got '{component['metadata']['name']}'"


def test_validate_component():
    """Test component validation."""
    # Test valid component
    valid_component = {
        "apiVersion": "servicemodel.ext.grafana.com/v1alpha1",
        "kind": "Component",
        "metadata": {
            "name": "test-service",
            "annotations": {
                "pagerduty.com/service-id": "P123456",
                "pagerduty.com/status": "active",
            },
        },
        "spec": {"type": "service", "description": "A test service"},
    }
    errors = _validate_component(valid_component)
    assert errors == []

    # Test missing required field
    invalid_component = valid_component.copy()
    del invalid_component["spec"]
    errors = _validate_component(invalid_component)
    assert "Missing required field: spec" in errors
