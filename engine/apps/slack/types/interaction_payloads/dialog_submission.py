"""
[Documentation](https://api.slack.com/dialogs)
"""


import typing

from apps.slack.types.common import BaseEvent, PayloadType


class DialogSubmissionPayload(BaseEvent):
    """
    [Documentation](https://api.slack.com/dialogs#:~:text=deeper%20at%20those-,attributes,-%2C%20which%20you%20might)
    """

    type: typing.Literal[PayloadType.DIALOG_SUBMISSION]
    """
    to differentiate from other interactive components, look for the string value `dialog_submission`
    """

    submission: typing.Dict[str, str]
    """
    A hash of key/value pairs representing the user's submission. Each key is a `name` field your app provided when
    composing the form. Each `value` is the user's submitted value, or in the case of a static select menu, the
    value you assigned to a specific response. The selection from a dynamic menu, the `value` can be a channel ID,
    user ID, etc.
    """

    state: str
    """
    this string simply echoes back what your app passed to `dialog.open`. Use it as a pointer that references sensitive data stored elsewhere.
    """

    action_ts: str
    """
    this is a unique identifier for this specific action occurrence generated by Slack. It can be evaluated as a timestamp with milliseconds if that is helpful to you
    """
