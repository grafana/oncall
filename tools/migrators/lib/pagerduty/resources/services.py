"""
PagerDuty services resource module.

This module provides functions for fetching PagerDuty services and extracting
relevant metadata for migration to Grafana's service model.
"""

from typing import Dict, List, Optional, Any
from pdpyras import APISession
import os

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


def fetch_services(session: APISession, include_integrations: bool = True,
                  include_teams: bool = True) -> List[TechnicalService]:
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

    params = {}
    if include_params:
        params["include[]"] = include_params

    # Fetch all services with the specified includes
    services_data = session.list_all("services", params=params)

    # Convert to TechnicalService objects
    services = [TechnicalService(service) for service in services_data]

    return services


def fetch_service_dependencies(session: APISession, services: List[TechnicalService]) -> None:
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
            if hasattr(response, 'json'):
                dependencies_data = response.json()

            # Extract relationships from the response
            if dependencies_data and isinstance(dependencies_data, dict) and "relationships" in dependencies_data:
                for relationship in dependencies_data["relationships"]:
                    # A dependency relationship has a supporting_service that the current service depends on
                    if "supporting_service" in relationship:
                        dep_id = relationship["supporting_service"]["id"]
                        if dep_id in service_map and dep_id != service.id:  # Avoid self-references
                            service.dependencies.append(service_map[dep_id])
            else:
                print(f"No valid relationship data found for service {service.name} (ID: {service.id})")

        except Exception as e:
            # Log but continue if we can't fetch dependencies for a service
            print(f"Error fetching dependencies for service {service.name}: {e}")

    print(f"Completed fetching dependencies for {len(services)} services.")


def get_all_technical_services_with_metadata(session: APISession) -> List[TechnicalService]:
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