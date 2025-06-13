import json
import re
from typing import Any, Dict, List, Optional, Union

from pdpyras import APISession

from lib.common.report import TAB
from lib.grafana.service_model_client import ServiceModelClient
from lib.pagerduty.config import (
    PAGERDUTY_FILTER_SERVICE_REGEX,
    PAGERDUTY_FILTER_TEAM,
    PAGERDUTY_FILTER_USERS,
)
from lib.pagerduty.report import format_service


def filter_services(services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter services based on configured filters.

    Args:
        services: List of service dictionaries to filter

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
                        if target["type"] == "user_reference":
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
            print(f"{TAB}Service {service['id']}: {reason}")

    if filtered_out > 0:
        print(f"Filtered out {filtered_out} services")

    return filtered_services


class BusinessService:
    """Class representing a PagerDuty business service with all necessary metadata."""

    def __init__(self, service_data: Dict[str, Any]):
        """
        Initialize a PagerDuty business service from API data.

        Args:
            service_data: Raw business service data from the PagerDuty API
        """
        self.id = service_data.get("id")
        self.name = service_data.get("name", "")
        self.description = service_data.get("description", "")
        self.point_of_contact = service_data.get("point_of_contact", "")
        self.created_at = service_data.get("created_at")
        self.updated_at = service_data.get("updated_at")

        # URLs and permalinks
        self.html_url = service_data.get("html_url")
        self.self_url = service_data.get("self")

        # Related entities
        self.teams = service_data.get("teams", [])

        # Dependencies - will be populated separately
        self.dependencies = []

        # Store raw data for access to any fields we might need later
        self.raw_data = service_data

    def __str__(self) -> str:
        return f"BusinessService(id={self.id}, name={self.name})"


class TechnicalService:
    """Class representing a PagerDuty technical service with all necessary metadata for migration."""

    def __init__(self, service_data: Dict[str, Any]):
        """
        Initialize a PagerDuty technical service from API data.

        Args:
            service_data: Raw service data from the PagerDuty API
        """
        self.id = service_data.get("id")
        self.name = service_data.get("name", "")
        self.description = service_data.get("description", "")
        self.status = service_data.get("status", "")
        self.created_at = service_data.get("created_at")
        self.updated_at = service_data.get("updated_at")

        # URLs and permalinks
        self.html_url = service_data.get("html_url")
        self.self_url = service_data.get("self")

        # Related entities
        self.escalation_policy = service_data.get("escalation_policy", {})
        self.teams = service_data.get("teams", [])

        # Dependencies - will be populated separately
        self.dependencies = []

        # Store raw data for access to any fields we might need later
        self.raw_data = service_data

    def __str__(self) -> str:
        return f"TechnicalService(id={self.id}, name={self.name})"


def fetch_services(
    session: APISession, include_integrations: bool = True, include_teams: bool = True
) -> List[TechnicalService]:
    """
    Fetch all PagerDuty technical services with their metadata.

    Args:
        session: Authenticated PagerDuty API session
        include_integrations: Whether to include integrations data
        include_teams: Whether to include teams data

    Returns:
        List of TechnicalService objects
    """
    include_params = []
    if include_integrations:
        include_params.append("integrations")
    if include_teams:
        include_params.append("teams")

    include_params.append("escalation_policies")
    params = {}
    if include_params:
        params["include[]"] = include_params

    # Fetch all services with the specified includes
    services_data = session.list_all("services", params=params)

    # Convert to TechnicalService objects
    services = [TechnicalService(service) for service in services_data]

    return services


def fetch_service_dependencies(
    session: APISession, services: List[TechnicalService]
) -> None:
    """
    Fetch and populate service dependencies using PagerDuty's service dependencies API.

    This function modifies the provided services list in-place by populating
    the dependencies field for each service.

    Args:
        session: Authenticated PagerDuty API session
        services: List of TechnicalService objects to update with dependencies
    """
    # Create a mapping of service_id to service for efficient lookup
    service_map = {service.id: service for service in services}

    print("Fetching service dependencies...")

    # Process each service to find its dependencies
    for service in services:
        try:
            # Use the service dependencies endpoint for technical services
            # Format: https://api.pagerduty.com/service_dependencies/technical_services/{id}
            response = session.get(
                f"service_dependencies/technical_services/{service.id}"
            )

            # Parse the response - depending on how pdpyras works, this might already be parsed
            # If it's already a dict, this will just use it as is
            dependencies_data = response
            if hasattr(response, "json"):
                dependencies_data = response.json()

            # Extract relationships from the response
            if (
                dependencies_data
                and isinstance(dependencies_data, dict)
                and "relationships" in dependencies_data
            ):
                for relationship in dependencies_data["relationships"]:
                    # A dependency relationship has a supporting_service that the current service depends on
                    if "supporting_service" in relationship:
                        dep_id = relationship["supporting_service"]["id"]
                        if (
                            dep_id in service_map and dep_id != service.id
                        ):  # Avoid self-references
                            service.dependencies.append(service_map[dep_id])
            else:
                print(
                    f"No valid relationship data found for service {service.name} (ID: {service.id})"
                )

        except Exception as e:
            # Log but continue if we can't fetch dependencies for a service
            print(f"Error fetching dependencies for service {service.name}: {e}")

    print(f"Completed fetching dependencies for {len(services)} services.")


def fetch_business_services(session: APISession) -> List[BusinessService]:
    """
    Fetch all PagerDuty business services with their metadata.

    Args:
        session: Authenticated PagerDuty API session

    Returns:
        List of BusinessService objects
    """
    # Fetch all business services
    services_data = session.list_all("business_services")

    # Convert to BusinessService objects
    services = [BusinessService(service) for service in services_data]

    return services


def get_all_technical_services_with_metadata(
    session: APISession,
) -> List[TechnicalService]:
    """
    Fetch all PagerDuty technical services with complete metadata including dependencies.

    This is the main function that should be used by the migration process.

    Args:
        session: Authenticated PagerDuty API session

    Returns:
        List of TechnicalService objects with all required metadata
    """
    # Fetch services with their basic metadata
    services = fetch_services(session)

    # Fetch and populate dependencies
    fetch_service_dependencies(session, services)

    return services


def fetch_business_service_dependencies(
    session: APISession,
    business_services: List[BusinessService],
    technical_services: Dict[str, Any],
) -> None:
    """
    Fetch and populate business service dependencies on technical services.

    This function modifies the provided business services list in-place by populating
    the dependencies field for each service.

    Args:
        session: Authenticated PagerDuty API session
        business_services: List of BusinessService objects to update with dependencies
        technical_services: Dictionary mapping service IDs to technical service objects
    """
    print("Fetching business service dependencies...")

    # Process each business service to find its dependencies
    for service in business_services:
        try:
            # Use the business service dependencies endpoint
            response = session.get(
                f"service_dependencies/business_services/{service.id}"
            )

            # Parse the response
            dependencies_data = response
            if hasattr(response, "json"):
                dependencies_data = response.json()

            # Extract relationships from the response
            if (
                dependencies_data
                and isinstance(dependencies_data, dict)
                and "relationships" in dependencies_data
            ):
                for relationship in dependencies_data["relationships"]:
                    # A dependency relationship has a supporting_service that the business service depends on
                    if "supporting_service" in relationship:
                        dep_id = relationship["supporting_service"]["id"]
                        if (
                            dep_id in technical_services
                        ):  # Only add if it's a technical service
                            service.dependencies.append(technical_services[dep_id])
            else:
                print(
                    f"No valid relationship data found for business service {service.name} (ID: {service.id})"
                )

        except Exception as e:
            # Log but continue if we can't fetch dependencies for a service
            print(
                f"Error fetching dependencies for business service {service.name}: {e}"
            )

    print(
        f"Completed fetching dependencies for {len(business_services)} business services."
    )


def get_all_business_services_with_metadata(
    session: APISession, technical_services: Dict[str, Any]
) -> List[BusinessService]:
    """
    Fetch all PagerDuty business services with complete metadata including dependencies.

    Args:
        session: Authenticated PagerDuty API session
        technical_services: Dictionary mapping service IDs to technical service objects

    Returns:
        List of BusinessService objects with all required metadata
    """
    # Fetch business services with their basic metadata
    business_services = fetch_business_services(session)

    # Fetch and populate dependencies
    fetch_business_service_dependencies(session, business_services, technical_services)

    return business_services


def _migrate_service_batch(
    client: ServiceModelClient,
    services: List[Any],
    migrate_func: callable,
    dry_run: bool = False,
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
    dry_run: bool = False,
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
                    "name": created_components[dep.id]["metadata"]["name"],
                }
                for dep in service.dependencies
                if dep.id in created_components
            ]

            if depends_on_refs:
                # Create patch payload with only the dependsOnRefs field
                patch_payload = {"spec": {"dependsOnRefs": depends_on_refs}}

                if not dry_run:
                    try:
                        client.patch_component(component_name, patch_payload)
                        print(f"Updated dependencies for service: {service.name}")
                    except Exception as e:
                        print(
                            f"Failed to update dependencies for service {service.name}: {e}"
                        )
                        # Log the full error details for debugging
                        print(f"Patch payload: {json.dumps(patch_payload, indent=2)}")


def _transform_service(
    service: Union[TechnicalService, BusinessService]
) -> Dict[str, Any]:
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

    service_name = re.sub("[^-a-zA-Z0-9.]", "-", service.name)
    service_name = re.sub(
        "-+", "-", service_name
    )  # Collapse multiple dashes to single dash
    service_name = re.sub(
        "^-+|-+$", "", service_name
    )  # Remove leading and trailing dashes
    # Create the base component structure
    component = {
        "apiVersion": "servicemodel.ext.grafana.com/v1alpha1",
        "kind": "Component",
        "metadata": {
            "name": service_name.lower(),  # Convert to k8s-friendly name
            "annotations": {"pagerduty.com/service-id": service.id},
        },
        "spec": {"type": service_type, "description": service.description},
    }

    # Add status annotation for technical services
    if is_technical and hasattr(service, "status"):
        component["metadata"]["annotations"]["pagerduty.com/status"] = service.status

    # Add PagerDuty URLs to annotations
    if service.html_url:
        component["metadata"]["annotations"][
            "pagerduty.com/html-url"
        ] = service.html_url
    if service.self_url:
        component["metadata"]["annotations"]["pagerduty.com/api-url"] = service.self_url

    return component


def _validate_component(component: Dict[str, Any]) -> List[str]:
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
        ("spec", dict),
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
        if (
            component["spec"]["type"] == "service"
            and "pagerduty.com/status" not in annotations
        ):
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


def _migrate_technical_service(
    client: ServiceModelClient, service: TechnicalService, dry_run: bool = False
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
        component = _transform_service(service)

        # Check if component already exists
        existing = client.get_component(component["metadata"]["name"])
        if existing:
            print(TAB + format_service(service, True) + " (preserved)")
            service.preserved = True
            service.migration_errors = None
            return existing

        # Validate the transformed component
        errors = _validate_component(component)
        if errors:
            service.migration_errors = errors
            service.preserved = False
            print(TAB + format_service(service, True))
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
        print(TAB + format_service(service, True))
        return None


def _migrate_business_service(
    client: ServiceModelClient, service: BusinessService, dry_run: bool = False
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
        component = _transform_service(service)

        # Check if component already exists
        existing = client.get_component(component["metadata"]["name"])
        if existing:
            print(TAB + format_service(service, True) + " (preserved)")
            service.preserved = True
            service.migration_errors = None
            return existing

        # Validate the transformed component
        errors = _validate_component(component)
        if errors:
            service.migration_errors = errors
            service.preserved = False
            print(TAB + format_service(service, True))
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
        print(TAB + format_service(service, True))
        return None


def migrate_all_services(
    client: ServiceModelClient,
    technical_services: List[TechnicalService],
    business_services: List[BusinessService],
    dry_run: bool = False,
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

    # Migrate technical services
    tech_components = _migrate_service_batch(
        client, technical_services, _migrate_technical_service, dry_run
    )

    # Migrate business services
    bus_components = _migrate_service_batch(
        client, business_services, _migrate_business_service, dry_run
    )

    # Update dependencies
    created_components = {**tech_components, **bus_components}
    _update_service_dependencies(
        client, technical_services + business_services, created_components, dry_run
    )

    return
