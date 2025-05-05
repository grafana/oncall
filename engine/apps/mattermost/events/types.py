import enum
import typing


class MattermostAlertGroupContext(typing.TypedDict):
    action: str
    token: str
    alert: str


class MattermostEvent(typing.TypedDict):
    user_id: str
    user_name: str
    channel_id: str
    channel_name: str
    team_id: str
    team_domain: str
    post_id: str
    trigger_id: str
    type: str
    data_source: str
    context: MattermostAlertGroupContext


class EventAction(enum.StrEnum):
    ACKNOWLEDGE = "acknowledge"
    UNACKNOWLEDGE = "unacknowledge"
    RESOLVE = "resolve"
    UNRESOLVE = "unresolve"
