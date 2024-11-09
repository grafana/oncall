from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SyncPermission:
    action: str


@dataclass
class SyncUser:
    id: int
    name: str
    login: str
    email: str
    role: str
    avatar_url: str
    permissions: List[SyncPermission]
    teams: Optional[List[int]]


@dataclass
class SyncTeam:
    team_id: int
    name: str
    email: str
    avatar_url: str


@dataclass
class SyncSettings:
    stack_id: int
    org_id: int
    license: str
    oncall_api_url: str
    oncall_token: str
    grafana_url: str
    grafana_token: str
    rbac_enabled: bool
    incident_enabled: bool
    incident_backend_url: str
    labels_enabled: bool
    irm_enabled: bool


@dataclass
class SyncData:
    users: List[SyncUser]
    teams: List[SyncTeam]
    team_members: Dict[int, List[int]]
    settings: SyncSettings
