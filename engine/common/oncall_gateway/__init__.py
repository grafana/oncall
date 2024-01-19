"""
This package is for interaction with OnCall-Gateway, service to provide multiregional chatops.
"""

from .utils import (  # noqa: F401
    can_link_slack_team,
    check_slack_installation_possible,
    create_oncall_connector,
    create_slack_connector,
    delete_oncall_connector,
    delete_slack_connector,
    link_slack_team,
    register_oncall_tenant,
    unlink_slack_team,
    unregister_oncall_tenant,
)
