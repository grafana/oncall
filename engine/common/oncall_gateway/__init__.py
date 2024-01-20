"""
This package is for interaction with OnCall-Gateway, service to provide multiregional chatops.
"""

from .utils import (  # noqa: F401
    can_link_slack_team_wrapper,
    link_slack_team_wrapper,
    register_oncall_tenant_wrapper,
    unlink_slack_team_wrapper,
    unregister_oncall_tenant_wrapper,
)
