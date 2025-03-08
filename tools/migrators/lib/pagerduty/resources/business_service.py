"""
PagerDuty business service resources.

This module provides classes and functions for interacting with PagerDuty business services.
"""

from typing import Any, Dict, List

from pdpyras import APISession


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
