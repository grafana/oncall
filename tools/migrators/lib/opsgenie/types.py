from typing import List, Literal, Optional, TypedDict


class OpsGenieUser(TypedDict):
    id: str
    username: str
    fullName: str
    role: dict
    timeZone: str
    locale: str
    userAddress: dict
    createdAt: str
    blocked: bool
    verified: bool
    notification_rules: List[dict]
    oncall_user: Optional[dict]


class OpsGenieSchedule(TypedDict):
    id: str
    name: str
    description: str
    timezone: str
    enabled: bool
    ownerTeam: dict
    rotations: List[dict]
    oncall_schedule: Optional[dict]
    migration_errors: List[str]


class OpsGenieEscalationPolicy(TypedDict):
    id: str
    name: str
    description: str
    ownerTeam: dict
    rules: List[dict]
    oncall_escalation_chain: Optional[dict]


class OpsGenieTeam(TypedDict):
    id: str
    name: str
    description: str
    members: List[dict]


class OpsGenieIntegration(TypedDict):
    id: str
    name: str
    type: str
    enabled: bool
    ownerTeam: dict
    isGlobal: bool
    status: dict
    oncall_integration: Optional[dict]


class OpsGenieService(TypedDict):
    id: str
    name: str
    description: str
    team: dict
    status: Literal["active", "maintenance", "disabled"]
    escalation: dict
