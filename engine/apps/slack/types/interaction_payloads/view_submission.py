"""
[Documentation](https://api.slack.com/reference/interaction-payloads/views#view_submission)
"""

import typing

from apps.slack.types.common import BaseEvent, PayloadType
from apps.slack.types.views import ModalView


class ViewSubmissionPayload(BaseEvent):
    """
    [Documentation](https://api.slack.com/reference/interaction-payloads/views#view_submission)
    """

    type: typing.Literal[PayloadType.VIEW_SUBMISSION]
    """
    Identifies the source of the payload. The type for this interaction is `view_submission`.
    """

    view: ModalView
    """
    The source [view](https://api.slack.com/surfaces/modals#views) of the modal the user submitted.
    """
