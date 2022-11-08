"""
This package is for interaction with OnCall-Gateway, service to provide multiregional chatops.
"""

from .tasks import delete_oncall_connector_async, delete_slack_connector_async  # noqa: F401
from .utils import check_slack_installation_backend, create_oncall_connector, create_slack_connector  # noqa: F401
