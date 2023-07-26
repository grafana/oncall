"""errors contains business-logic error codes for internal api.

It's expected that error codes will use 1000-9999 codes range, where first two digits are for entity:
11xx - AlertGroup, 12xx - AlertReceiveChannel, etc.
10xx are saved for non-entity related errors.
"""
# TODO: this package is WIP. It requires validation of code ranges.
from enum import Enum, unique


@unique
class AlertGroupAPIError(Enum):
    """
    Error codes for alert group.
    Range is 1100-1199
    """

    RESOLUTION_NOTE_REQUIRED = 1101
