from urllib.parse import urlparse

import kubernetes
from kubernetes import client

from lib.base_config import GRAFANA_SERVICE_ACCOUNT_URL

SERVICE_MODEL_API_GROUP = "servicemodel.ext.grafana.com"
SERVICE_MODEL_API_VERSION = "v1alpha1"


class ServiceModelClient:
    """
    Client for interacting with Grafana's Service Model API using the Kubernetes client.
    This uses the k8s API to interact with the service model which is implemented
    as a Kubernetes ApiServer embedded within Grafana.
    """

    @staticmethod
    def parse_k8s_url(url: str) -> tuple:
        """
        Parse a kubernetes URL of the format https://<namespace>:<token>@<server>
        Returns tuple of (server_url, namespace, token)
        """
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(
                "Invalid URL format. Expected: https://<namespace>:<token>@<server>"
            )

        # Split username (namespace) and password (token)
        if "@" not in parsed.netloc:
            raise ValueError(
                "URL must contain credentials in the format namespace:token@server"
            )

        auth, server = parsed.netloc.rsplit("@", 1)
        if ":" not in auth:
            raise ValueError("Credentials must be in the format namespace:token")

        namespace, token = auth.split(":", 1)

        # Reconstruct server URL with scheme
        server_url = f"{parsed.scheme}://{server}{parsed.path}"

        return server_url, namespace, token

    def __init__(self):
        """
        Initialize the ServiceModelClient.
        Configures the client using a URL-based format or falls back to legacy configuration.
        """
        if GRAFANA_SERVICE_ACCOUNT_URL:
            try:
                server_url, namespace, token = self.parse_k8s_url(
                    GRAFANA_SERVICE_ACCOUNT_URL
                )

                # Configure client using parsed parameters
                configuration = client.Configuration()
                configuration.host = server_url
                configuration.api_key = {"authorization": f"Bearer {token}"}
                # configuration.verify_ssl = False  # Note: In production, you should handle SSL verification properly

                # Set the default namespace
                self.default_namespace = namespace

                # Create API client with custom configuration
                client.Configuration.set_default(configuration)
                self.api_client = client.ApiClient(configuration)

            except ValueError as e:
                raise ValueError(
                    f"Failed to parse GRAFANA_SERVICE_ACCOUNT_URL: {str(e)}"
                )
        else:
            raise ValueError(
                "Unable to configure Kubernetes client. Please set: "
                "GRAFANA_SERVICE_ACCOUNT_URL (format: https://<namespace>:<token>@<server>) "
            )

        # Base API group and version for service model resources
        self.api_group = SERVICE_MODEL_API_GROUP
        self.api_version = SERVICE_MODEL_API_VERSION

        # Initialize the CustomObjectsApi for interacting with custom resources
        self.custom_api = client.CustomObjectsApi(self.api_client)

    def get_components(self, namespace=None):
        """
        Get all Component resources from the service model.

        Args:
            namespace: The namespace to list components from. Defaults to the namespace from the URL.

        Returns:
            List of Component resources.
        """
        namespace = namespace or self.default_namespace
        return self.custom_api.list_namespaced_custom_object(
            group=self.api_group,
            version=self.api_version,
            namespace=namespace,
            plural="components",
        )

    def get_component(self, name, namespace=None):
        """
        Get a specific Component resource by name.

        Args:
            name: The name of the component.
            namespace: The namespace of the component.

        Returns:
            The Component resource if found, None otherwise.
        """
        namespace = namespace or self.default_namespace
        try:
            return self.custom_api.get_namespaced_custom_object(
                group=self.api_group,
                version=self.api_version,
                namespace=namespace,
                plural="components",
                name=name,
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_component(self, component_data, namespace=None):
        """
        Create a new Component resource.

        Args:
            component_data: The Component resource data.
            namespace: The namespace to create the component in.

        Returns:
            The created Component resource.
        """
        namespace = namespace or self.default_namespace
        return self.custom_api.create_namespaced_custom_object(
            group=self.api_group,
            version=self.api_version,
            namespace=namespace,
            plural="components",
            body=component_data,
        )

    def update_component(self, name, component_data, namespace=None):
        """
        Update an existing Component resource.

        Args:
            name: The name of the component to update.
            component_data: The updated Component resource data.
            namespace: The namespace of the component.

        Returns:
            The updated Component resource.
        """
        namespace = namespace or self.default_namespace
        return self.custom_api.replace_namespaced_custom_object(
            group=self.api_group,
            version=self.api_version,
            namespace=namespace,
            plural="components",
            name=name,
            body=component_data,
        )

    def patch_component(self, name, patch_data, namespace=None):
        """
        Patch an existing Component resource.

        Args:
            name: The name of the component to patch.
            patch_data: The patch data to apply.
            namespace: The namespace of the component.

        Returns:
            The patched Component resource.
        """
        namespace = namespace or self.default_namespace
        return self.custom_api.patch_namespaced_custom_object(
            group=self.api_group,
            version=self.api_version,
            namespace=namespace,
            plural="components",
            name=name,
            body=patch_data,
        )
