"""
Unit tests for the Grafana Service Model transformation logic.
"""

from unittest.mock import Mock

import pytest

from lib.grafana.transform import transform_service, validate_component
from lib.pagerduty.resources.business_service import BusinessService
from lib.pagerduty.resources.services import TechnicalService


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


def test_transform_technical_service(technical_service):
    """Test transforming a technical service."""
    component = transform_service(technical_service)

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
    component = transform_service(business_service)

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
    errors = validate_component(valid_component)
    assert errors == []

    # Test missing required field
    invalid_component = valid_component.copy()
    del invalid_component["spec"]
    errors = validate_component(invalid_component)
    assert "Missing required field: spec" in errors
