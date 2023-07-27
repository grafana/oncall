import typing

from .common import PayloadType


class ViewSubmissionEvent(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/reference/interaction-payloads/views#view_submission)
    """

    type: typing.Literal[PayloadType.VIEW_SUBMISSION]
    """
    Identifies the source of the payload. The type for this interaction is `view_submission`.
    """
