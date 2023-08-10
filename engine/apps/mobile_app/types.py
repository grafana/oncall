import typing
from enum import StrEnum


class MessageType(StrEnum):
    DEFAULT = "oncall.message"
    IMPORTANT = "oncall.critical_message"
    INFO = "oncall.info"


class Platform(StrEnum):
    ANDROID = "android"
    IOS = "ios"


class FCMMessageData(typing.TypedDict):
    title: str
    subtitle: typing.Optional[str]
    body: typing.Optional[str]
