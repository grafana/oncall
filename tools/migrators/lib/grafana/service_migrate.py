"""
Migration logic for converting PagerDuty services to Grafana's service model.

This module provides functions to migrate PagerDuty services to Grafana's service model,
including creating the required 'pagerduty' Group and handling both individual and batch migrations.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pdpyras import APISession
from lib.pagerduty.resources.services import TechnicalService, get_all_technical_services_with_metadata
from lib.pagerduty.resources.business_service import BusinessService, get_all_business_services_with_metadata
from lib.grafana.service_model_client import ServiceModelClient
from lib.common.report import TAB
from lib.grafana.transform import (
    transform_service,
    validate_component

)
from lib.pagerduty.report import format_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_technical_service(
    client: ServiceModelClient,
    service: TechnicalService,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Migrate a single technical service to Grafana's service model.

    Args:
        client: The ServiceModelClient to use
        service: The technical service to migrate
        dry_run: If True, only validate and log what would be done

    Returns:
        The created component if successful, None otherwise
    """
    try:
        # Transform the service
        component = transform_service(service)

        # Check if component already exists
        existing = client.get_component(component["metadata"]["name"])
        if existing:
            print(TAB + format_service(service, True) + " (preserved)")
            service.preserved = True
            service.migration_errors = None
            return existing

        # Validate the transformed component
        errors = validate_component(component)
        if errors:
            service.migration_errors = errors
            service.preserved = False
            print(TAB + format_service(service, False))
            return None

        if dry_run:
            service.migration_errors = None
            service.preserved = False
            print(TAB + format_service(service, True) + " (would create)")
            return component

        # Create the component
        created = client.create_component(component)
        service.migration_errors = None
        service.preserved = False
        print(TAB + format_service(service, True) + " (created)")
        return created

    except Exception as e:
        service.migration_errors = str(e)
        service.preserved = False
        print(TAB + format_service(service, False))
        return None


def migrate_business_service(
    client: ServiceModelClient,
    service: BusinessService,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Migrate a single business service to Grafana's service model.

    Args:
        client: The ServiceModelClient to use
        service: The business service to migrate
        dry_run: If True, only validate and log what would be done

    Returns:
        The created component if successful, None otherwise
    """
    try:
        # Transform the service
        component = transform_service(service)

        # Check if component already exists
        existing = client.get_component(component["metadata"]["name"])
        if existing:
            print(TAB + format_service(service, True) + " (preserved)")
            service.preserved = True
            service.migration_errors = None
            return existing

        # Validate the transformed component
        errors = validate_component(component)
        if errors:
            service.migration_errors = errors
            service.preserved = False
            print(TAB + format_service(service, False))
            return None

        if dry_run:
            service.migration_errors = None
            service.preserved = False
            print(TAB + format_service(service, True) + " (would create)")
            return component

        # Create the component
        created = client.create_component(component)
        service.migration_errors = None
        service.preserved = False
        print(TAB + format_service(service, True) + " (created)")
        return created

    except Exception as e:
        service.migration_errors = str(e)
        service.preserved = False
        print(TAB + format_service(service, False))
        return None


def _migrate_service_batch(
    client: ServiceModelClient,
    services: List[Any],
    migrate_func: callable,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate a batch of services using the provided migration function.

    Args:
        client: The ServiceModelClient to use
        services: List of services to migrate
        migrate_func: Function to use for migrating each service
        dry_run: If True, only validate and log what would be done

    Returns:
        Dictionary containing migration statistics and created components
    """
    created_components = {}

    for service in services:
        component = migrate_func(client, service, dry_run)
        if component:
            created_components[service.id] = component

    return created_components


def _update_service_dependencies(
    client: ServiceModelClient,
    services: List[Any],
    created_components: Dict[str, Any],
    dry_run: bool = False
) -> None:
    """
    Update dependencies for all services with proper refs.

    Args:
        client: The ServiceModelClient to use
        services: List of services to update
        created_components: Dictionary of created components by service ID
        dry_run: If True, only validate and log what would be done
    """
    for service in services:
        if service.id in created_components and service.dependencies:
            component_name = created_components[service.id]["metadata"]["name"]

            depends_on_refs = [
                {
                    "apiVersion": "servicemodel.ext.grafana.com/v1alpha1",
                    "kind": "Component",
                    "name": created_components[dep.id]["metadata"]["name"]
                }
                for dep in service.dependencies
                if dep.id in created_components
            ]

            if depends_on_refs:
                # Create patch payload with only the dependsOnRefs field
                patch_payload = {
                    "spec": {
                        "dependsOnRefs": depends_on_refs
                    }
                }

                if not dry_run:
                    try:
                        client.patch_component(component_name, patch_payload)
                        print(f"Updated dependencies for service: {service.name}")
                    except Exception as e:
                        print(f"Failed to update dependencies for service {service.name}: {e}")
                        # Log the full error details for debugging
                        print(f"Patch payload: {json.dumps(patch_payload, indent=2)}")


def migrate_all_services(
    client: ServiceModelClient,
    technical_services: List[TechnicalService],
    business_services: List[BusinessService],
    dry_run: bool = False
) -> None:
    """
    Migrate all PagerDuty services to Grafana's service model.

    Args:
        client: The ServiceModelClient to use
        technical_services: List of technical services to migrate
        business_services: List of business services to migrate
        dry_run: If True, only validate and log what would be done

    Returns:
        Dictionary containing migration statistics
    """
    stats = {
        "technical_services": {"total": 0, "successful": 0, "failed": 0},
        "business_services": {"total": 0, "successful": 0, "failed": 0}
    }

    # Migrate technical services
    tech_components = _migrate_service_batch(
        client, technical_services, migrate_technical_service, dry_run
    )

    # Migrate business services
    bus_components = _migrate_service_batch(
        client, business_services, migrate_business_service, dry_run
    )

    # Update dependencies
    created_components = {**tech_components, **bus_components}
    _update_service_dependencies(
        client, technical_services + business_services, created_components, dry_run
    )

    return
