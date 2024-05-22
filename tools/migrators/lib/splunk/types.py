import typing

from lib.oncall import types as oncall_types


class SplunkUserPagingPolicy(typing.TypedDict):
    order: int
    timeout: int
    contactType: typing.Literal["sms", "phone", "email", "push"]
    extId: str


class SplunkUserWithPagingPolicies(typing.TypedDict):
    firstName: str
    lastName: str
    displayName: str
    username: str
    email: str
    createdAt: str
    pagingPolicies: typing.NotRequired[typing.List[SplunkUserPagingPolicy]]
    oncall_user: typing.NotRequired[oncall_types.OnCallUser]


class SplunkTeamMember(typing.TypedDict):
    username: str
    firstName: str
    lastName: str
    displayName: str
    version: int
    verified: bool


class SplunkTeam(typing.TypedDict):
    name: str
    slug: str
    memberCount: int
    version: int
    isDefaultTeam: bool
    description: str
    members: typing.NotRequired[typing.List[SplunkTeamMember]]


class SplunkSchedulePolicy(typing.TypedDict):
    name: str
    slug: str


class _SplunkScheduleOnCallUser(typing.TypedDict):
    username: str


class SplunkRotationShiftMask(typing.TypedDict):
    class SplunkRotationShiftMaskDay(typing.TypedDict):
        m: bool
        t: bool
        w: bool
        th: bool
        f: bool
        sa: bool
        su: bool

    class SplunkRotationShiftMaskTime(typing.TypedDict):
        class SplunkRotationShiftMaskTime(typing.TypedDict):
            hour: int
            minute: int

        start: SplunkRotationShiftMaskTime
        end: SplunkRotationShiftMaskTime

    day: SplunkRotationShiftMaskDay
    time: typing.List[SplunkRotationShiftMaskTime]


class SplunkRotationShiftPeriod(typing.TypedDict):
    start: str
    end: str
    username: str
    isRoll: bool
    memberSlug: str


class SplunkRotationShiftMember(typing.TypedDict):
    username: str
    slug: str


class SplunkRotationShift(typing.TypedDict):
    label: str
    timezone: str
    start: str
    duration: int
    shifttype: typing.Literal["std", "pho", "cstm"]
    """
    - `std`: 24/7 shift
    - `pho`: partial day shift
    - `cstm`: multi-day shift
    """
    mask: SplunkRotationShiftMask
    mask2: typing.NotRequired[SplunkRotationShiftMask]
    mask3: typing.NotRequired[SplunkRotationShiftMask]
    periods: typing.List[SplunkRotationShiftPeriod]
    current: SplunkRotationShiftPeriod
    next: SplunkRotationShiftPeriod
    shiftMembers: typing.List[SplunkRotationShiftMember]


class SplunkRotation(typing.TypedDict):
    label: str
    totalMembersInRotation: int
    shifts: typing.List[SplunkRotationShift]


class SplunkScheduleOverride(typing.TypedDict):
    origOnCallUser: _SplunkScheduleOnCallUser
    overrideOnCallUser: _SplunkScheduleOnCallUser
    start: str
    end: str
    policy: SplunkSchedulePolicy


class SplunkSchedule(typing.TypedDict):
    class _SplunkSchedule(typing.TypedDict):
        start: str
        end: str
        onCallUser: _SplunkScheduleOnCallUser
        onCallType: str
        rolls: typing.List[typing.Any]

    name: typing.NotRequired[str]
    policy: SplunkSchedulePolicy
    schedule: typing.List[_SplunkSchedule]
    overrides: typing.List[SplunkScheduleOverride]
    oncall_schedule: typing.NotRequired[oncall_types.OnCallSchedule]
    migration_errors: typing.NotRequired[typing.List[str]]


class SplunkScheduleWithTeamAndRotations(SplunkSchedule):
    team: SplunkTeam
    rotations: typing.List[SplunkRotation]


class SplunkEscalationPolicyStepUser(typing.TypedDict):
    class _SplunkEscalationPolicyStepUser(typing.TypedDict):
        username: str
        firstName: str
        lastName: str

    executionType: typing.Literal["user"]
    user: _SplunkEscalationPolicyStepUser


class SplunkEscalationPolicyStepTeamPage(typing.TypedDict):
    executionType: typing.Literal["team_page"]


class SplunkEscalationPolicyStepRotationGroup(typing.TypedDict):
    """
    NOTE: we don't support migrating `rotation_group_next` and `rotation_group_previous` policy step types
    """

    class _SplunkEscalationPolicyStepRotationGroup(typing.TypedDict):
        slug: str
        label: str

    executionType: typing.Literal[
        "rotation_group", "rotation_group_next", "rotation_group_previous"
    ]
    rotationGroup: _SplunkEscalationPolicyStepRotationGroup


class SplunkEscalationPolicyStepEmail(typing.TypedDict):
    """
    NOTE: we don't support migrating this type of escalation policy step
    """

    class _SplunkEscalationPolicyStepEmail(typing.TypedDict):
        address: str

    executionType: typing.Literal["email"]
    email: _SplunkEscalationPolicyStepEmail


class SplunkEscalationPolicyStepWebhook(typing.TypedDict):
    """
    NOTE: we don't support migrating this type of escalation policy step
    """

    class _SplunkEscalationPolicyStepWebhook(typing.TypedDict):
        slug: str
        label: str

    executionType: typing.Literal["webhook"]
    webhook: _SplunkEscalationPolicyStepWebhook


class SplunkEscalationPolicyStepPolicyRouting(typing.TypedDict):
    """
    NOTE: we don't support migrating this type of escalation policy step
    """

    class _SplunkEscalationPolicyStepPolicyRouting(typing.TypedDict):
        policySlug: str
        teamSlug: str

    executionType: typing.Literal["policy_routing"]
    targetPolicy: _SplunkEscalationPolicyStepPolicyRouting


SplunkEscalationPolicyStepEntry = typing.Union[
    SplunkEscalationPolicyStepUser,
    SplunkEscalationPolicyStepTeamPage,
    SplunkEscalationPolicyStepRotationGroup,
    SplunkEscalationPolicyStepEmail,
    SplunkEscalationPolicyStepWebhook,
    SplunkEscalationPolicyStepPolicyRouting,
]


class SplunkEscalationPolicyStep(typing.TypedDict):
    timeout: int
    entries: typing.List[SplunkEscalationPolicyStepEntry]


class SplunkEscalationPolicy(typing.TypedDict):
    name: str
    slug: str
    steps: typing.List[SplunkEscalationPolicyStep]
    ignoreCustomPagingPolicies: bool
    oncall_escalation_chain: typing.NotRequired[oncall_types.OnCallEscalationChain]
    unmatched_users: typing.NotRequired[typing.List[str]]
    flawed_schedules: typing.NotRequired[typing.List[str]]
    unsupported_escalation_entry_types: typing.NotRequired[typing.List[str]]
