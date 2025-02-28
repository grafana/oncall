"""
Transformation logic for converting PagerDuty services to Grafana Service Model format.

This module provides functions to transform PagerDuty technical and business services
into the Backstage Catalog format used by Grafana's Service Model.
"""

from typing import Dict, List, Any, Optional, Union
from lib.pagerduty.resources.services import TechnicalService
from lib.pagerduty.resources.business_service import BusinessService


def transform_service(service: Union[TechnicalService, BusinessService]) -> Dict[str, Any]:
    """
    Transform a PagerDuty service (technical or business) into a Backstage Component.

    Args:
        service: The PagerDuty service to transform (either TechnicalService or BusinessService)

    Returns:
        A dictionary containing the transformed service in Backstage Component format
    """
    # Determine service type and required fields
    is_technical = isinstance(service, TechnicalService)
    service_type = "service" if is_technical else "business_service"

    # Create the base component structure
    component = {
        "apiVersion": "servicemodel.ext.grafana.com/v1alpha1",
        "kind": "Component",
        "metadata": {
            "name": service.name.lower().replace(" ", "-"),  # Convert to k8s-friendly name
            "annotations": {
                "pagerduty.com/service-id": service.id
            }
        },
        "spec": {
            "type": service_type,
            "description": service.description
        }
    }

    # Add status annotation for technical services
    if is_technical and hasattr(service, "status"):
        component["metadata"]["annotations"]["pagerduty.com/status"] = service.status

    # Add PagerDuty URLs to annotations
    if service.html_url:
        component["metadata"]["annotations"]["pagerduty.com/html-url"] = service.html_url
    if service.self_url:
        component["metadata"]["annotations"]["pagerduty.com/api-url"] = service.self_url

    return component


def validate_component(component: Dict[str, Any]) -> List[str]:
    """
    Validate a transformed Component resource.

    Args:
        component: The Component resource to validate

    Returns:
        List of validation errors. Empty list means valid.
    """
    errors = []

    # Check required fields
    required_fields = [
        ("apiVersion", str),
        ("kind", str),
        ("metadata", dict),
        ("spec", dict)
    ]

    for field, field_type in required_fields:
        if field not in component:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(component[field], field_type):
            errors.append(f"Field {field} must be of type {field_type.__name__}")

    # If we're missing required fields, don't continue with deeper validation
    if errors:
        return errors

    # Check metadata requirements
    metadata = component["metadata"]
    if "name" not in metadata:
        errors.append("metadata.name is required")
    elif not isinstance(metadata["name"], str):
        errors.append("metadata.name must be a string")

    # Check required annotations
    if "annotations" not in metadata:
        errors.append("metadata.annotations is required")
    else:
        annotations = metadata["annotations"]
        if "pagerduty.com/service-id" not in annotations:
            errors.append("Required annotation missing: pagerduty.com/service-id")
        if component["spec"]["type"] == "service" and "pagerduty.com/status" not in annotations:
            errors.append("Required annotation missing: pagerduty.com/status")

    # Check spec requirements
    spec = component["spec"]
    if "type" not in spec:
        errors.append("spec.type is required")
    elif not isinstance(spec["type"], str):
        errors.append("spec.type must be a string")
    elif spec["type"] not in ["service", "business_service"]:
        errors.append("spec.type must be either 'service' or 'business_service'")

    return errors