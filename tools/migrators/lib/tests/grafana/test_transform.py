"""
Unit tests for the Grafana Service Model transformation logic.
"""

import unittest
from unittest.mock import Mock

from lib.grafana.transform import transform_service, validate_component
from lib.pagerduty.resources.business_service import BusinessService
from lib.pagerduty.resources.services import TechnicalService


class TestTransform(unittest.TestCase):
    """Test cases for the transformation functions."""

    def setUp(self):
        """Set up test data."""
        # Create a mock technical service
        self.technical_service = Mock(spec=TechnicalService)
        self.technical_service.name = "Test Service"
        self.technical_service.description = "A test service"
        self.technical_service.id = "P123456"
        self.technical_service.status = "active"
        self.technical_service.html_url = "https://pagerduty.com/services/P123456"
        self.technical_service.self_url = "https://api.pagerduty.com/services/P123456"

        # Create a mock business service
        self.business_service = Mock(spec=BusinessService)
        self.business_service.name = "Test Business Service"
        self.business_service.description = "A test business service"
        self.business_service.id = "P789012"
        self.business_service.html_url = "https://pagerduty.com/services/P789012"
        self.business_service.self_url = "https://api.pagerduty.com/services/P789012"

    def test_transform_technical_service(self):
        """Test transforming a technical service."""
        component = transform_service(self.technical_service)

        # Verify the component structure
        self.assertEqual(
            component["apiVersion"], "servicemodel.ext.grafana.com/v1alpha1"
        )
        self.assertEqual(component["kind"], "Component")
        self.assertEqual(component["metadata"]["name"], "test-service")
        self.assertEqual(component["spec"]["type"], "service")
        self.assertEqual(component["spec"]["description"], "A test service")

        # Verify annotations
        annotations = component["metadata"]["annotations"]
        self.assertEqual(annotations["pagerduty.com/service-id"], "P123456")
        self.assertEqual(annotations["pagerduty.com/status"], "active")
        self.assertEqual(
            annotations["pagerduty.com/html-url"],
            "https://pagerduty.com/services/P123456",
        )
        self.assertEqual(
            annotations["pagerduty.com/api-url"],
            "https://api.pagerduty.com/services/P123456",
        )

    def test_transform_business_service(self):
        """Test transforming a business service."""
        component = transform_service(self.business_service)

        # Verify the component structure
        self.assertEqual(
            component["apiVersion"], "servicemodel.ext.grafana.com/v1alpha1"
        )
        self.assertEqual(component["kind"], "Component")
        self.assertEqual(component["metadata"]["name"], "test-business-service")
        self.assertEqual(component["spec"]["type"], "business_service")
        self.assertEqual(component["spec"]["description"], "A test business service")

        # Verify annotations
        annotations = component["metadata"]["annotations"]
        self.assertEqual(annotations["pagerduty.com/service-id"], "P789012")
        self.assertEqual(
            annotations["pagerduty.com/html-url"],
            "https://pagerduty.com/services/P789012",
        )
        self.assertEqual(
            annotations["pagerduty.com/api-url"],
            "https://api.pagerduty.com/services/P789012",
        )

    def test_validate_component(self):
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
        self.assertEqual(errors, [])

        # Test missing required field
        invalid_component = valid_component.copy()
        del invalid_component["spec"]
        errors = validate_component(invalid_component)
        self.assertIn("Missing required field: spec", errors)


if __name__ == "__main__":
    unittest.main()
