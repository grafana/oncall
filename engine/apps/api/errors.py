"""errors contains business-logic error codes for internal api.

It's expected that error codes will use 1000-9999 codes range, where first two digits are for entity:
11xx - AlertGroup, 12xx - AlertReceiveChannel, etc.
10xx are saved for non-entity related errors.
"""
# TODO: this package is WIP. It requires validation of code ranges.
from enum import Enum, unique

from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse
from rest_framework.views import exception_handler as drf_exception_handler


class ExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        old_error_response_data = drf_exception_handler(self.exc, self.context).data
        # For the compatibility reasons, we are keeping the old format of error response
        # and adding the new format of error response in the same response.
        # This is done to avoid breaking the existing clients.
        # New format uses the default error response format from drf_standardized_errors.
        new_error_response_data = super().format_error_response(error_response)
        data = {**old_error_response_data, "new_format_data": new_error_response_data}
        return data


@unique
class AlertGroupAPIError(Enum):
    """
    Error codes for alert group.
    Range is 1100-1199
    """

    RESOLUTION_NOTE_REQUIRED = 1101
