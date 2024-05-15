import typing


class OnCallUserNotificationRule(typing.TypedDict):
    position: int
    id: str
    user_id: str
    important: bool
    type: str


class OnCallUser(typing.TypedDict):
    id: str
    email: str
    slack: typing.Optional[str]
    username: str
    role: str
    is_phone_number_verified: bool
    timezone: str
    teams: typing.List[str]
    notification_rules: typing.List[OnCallUserNotificationRule]


class OnCallSchedule(typing.TypedDict):
    pass


class OnCallEscalationChain(typing.TypedDict):
    id: str


class OnCallEscalationPolicyCreatePayload(typing.TypedDict):
    pass
