from unittest import mock

import pytest

from lib.splunk.resources import schedules

SPLUNK_USER1_ID = "joeyorlando"
SPLUNK_USER2_ID = "joeyorlando1"
ONCALL_USER1_ID = "UABCD12345"
ONCALL_USER2_ID = "UGEF903940"

DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP = {
    SPLUNK_USER1_ID: ONCALL_USER1_ID,
    SPLUNK_USER2_ID: ONCALL_USER2_ID,
}

ESCALATION_POLICY_NAME = "Example"
ROTATION_SHIFT_NAME = "simple rotation shift"
ONCALL_SCHEDULE_ID = "SABCD12345"
WEB_SOURCE = 0


def _generate_splunk_schedule_rotation_shift(
    shift_type="std",
    shift_name=ROTATION_SHIFT_NAME,
    start="2024-04-23T13:00:00Z",
    duration=7,
    mask=None,
    shift_members=None,
    **kwargs,
):
    return {
        "label": shift_name,
        "timezone": "America/Toronto",
        "start": start,
        "duration": duration,
        "shifttype": shift_type,
        "mask": mask,
        "periods": [],
        "current": {},
        "next": {},
        "shiftMembers": shift_members
        or [
            {
                "username": SPLUNK_USER1_ID,
                "slug": "rtm-YZTYP1lUogCUvftpIEpC",
            },
            {
                "username": SPLUNK_USER2_ID,
                "slug": "rtm-U8v2awNBaDTFlTavX86p",
            },
        ],
        **kwargs,
    }


def _generate_splunk_schedule_rotation_shift_mask(
    off_days=None, start_hour=0, start_minute=0, end_hour=0, end_minute=0
):
    off_days = off_days or []
    return {
        "day": {
            day: (day not in off_days) for day in ["m", "t", "w", "th", "f", "sa", "su"]
        },
        "time": [
            {
                "start": {
                    "hour": start_hour,
                    "minute": start_minute,
                },
                "end": {
                    "hour": end_hour,
                    "minute": end_minute,
                },
            },
        ],
    }


def _generate_full_day_splunk_schedule_rotation_shift(**kwargs):
    return _generate_splunk_schedule_rotation_shift(
        shift_type="std",
        mask=_generate_splunk_schedule_rotation_shift_mask(),
        **kwargs,
    )


def _generate_partial_day_splunk_schedule_rotation_shift(
    mask_off_days=None,
    mask_start_hour=0,
    mask_start_minute=0,
    mask_end_hour=0,
    mask_end_minute=0,
    duration=1,
    **kwargs,
):
    return _generate_splunk_schedule_rotation_shift(
        shift_type="pho",
        duration=duration,
        mask=_generate_splunk_schedule_rotation_shift_mask(
            off_days=mask_off_days,
            start_hour=mask_start_hour,
            start_minute=mask_start_minute,
            end_hour=mask_end_hour,
            end_minute=mask_end_minute,
        ),
        **kwargs,
    )


def _generate_multi_day_splunk_schedule_rotation_shift(mask, duration=7, **kwargs):
    return _generate_splunk_schedule_rotation_shift(
        shift_type="cstm",
        duration=duration,
        mask=mask,
        **kwargs,
    )


def _generate_splunk_schedule_rotation(shifts=None):
    return {
        "label": "abcdeg",
        "totalMembersInRotation": 2,
        "shifts": shifts or [_generate_full_day_splunk_schedule_rotation_shift()],
    }


def _generate_splunk_schedule_override(
    start="2024-05-01T15:00:00Z",
    end="2024-05-01T21:00:00Z",
    orig_oncall_user=SPLUNK_USER1_ID,
    override_oncall_user=SPLUNK_USER2_ID,
):
    return {
        "origOnCallUser": {
            "username": orig_oncall_user,
        },
        "overrideOnCallUser": {
            "username": override_oncall_user,
        },
        "start": start,
        "end": end,
        "policy": {
            "name": ESCALATION_POLICY_NAME,
            "slug": "pol-GiTwwwVXzUDtJbPu",
        },
    }


def _generate_schedule_name(name=ESCALATION_POLICY_NAME):
    return f"{name} schedule"


def _generate_splunk_schedule(rotations=None, overrides=None, oncall_schedule=None):
    team_name = "First Team"
    team_slug = "team-YVFyvc0gxEhVXEFj"

    schedule = {
        "name": _generate_schedule_name(),
        "policy": {
            "name": ESCALATION_POLICY_NAME,
            "slug": team_slug,
        },
        "schedule": [
            {
                "onCallUser": {
                    "username": SPLUNK_USER1_ID,
                },
                "onCallType": "rotation_group",
                "rotationName": "simple rotation",
                "shiftName": "simple rotation shift",
                "rolls": [],
            },
        ],
        "team": {
            "_selfUrl": f"/api-public/v1/team/{team_slug}",
            "_membersUrl": f"/api-public/v1/team/{team_slug}/members",
            "_policiesUrl": f"/api-public/v1/team/{team_slug}/policies",
            "_adminsUrl": f"/api-public/v1/team/{team_slug}/admins",
            "name": team_name,
            "slug": team_slug,
            "memberCount": 2,
            "version": 3,
            "isDefaultTeam": False,
            "description": "this is a description",
        },
        "rotations": rotations or [],
        "overrides": overrides or [],
    }

    if oncall_schedule:
        schedule["oncall_schedule"] = oncall_schedule

    return schedule


def _generate_oncall_schedule(id=ONCALL_SCHEDULE_ID, name=ESCALATION_POLICY_NAME):
    return {
        "id": id,
        "name": _generate_schedule_name(name),
    }


def _generate_rotation_missing_user_error_msg(
    user_id, rotation_name=ROTATION_SHIFT_NAME
):
    return f"{rotation_name}: Users with IDs ['{user_id}'] not found. The user(s) don't seem to exist in Grafana."


def _generate_override_missing_user_error_msg(user_id):
    return f"Override: User with ID '{user_id}' not found. The user doesn't seem to exist in Grafana."


def _generate_oncall_shift_create_api_payload(data):
    shift_type = data["type"]

    shift_base = {
        "type": shift_type,
        "team_id": None,
        "time_zone": "UTC",
        "source": WEB_SOURCE,
    }

    if shift_type == "rolling_users":
        shift_base.update(
            {
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "until": None,
            }
        )

    return {**shift_base, **data}


def _generate_oncall_schedule_create_api_payload(name, num_expected_shifts):
    return {
        "name": name,
        "type": "web",
        "team_id": None,
        "time_zone": "UTC",
        # these would be the string IDs of the oncall shifts created.. we'll just expect any value
        "shifts": [mock.ANY for _ in range(num_expected_shifts)],
    }


@pytest.mark.parametrize(
    "splunk_schedule,oncall_schedules,user_id_map,expected_oncall_schedule_match,expected_errors",
    [
        # oncall schedule matched, all user IDs matched, no errors
        (
            _generate_splunk_schedule(
                rotations=[_generate_splunk_schedule_rotation()],
                overrides=[_generate_splunk_schedule_override()],
            ),
            [_generate_oncall_schedule()],
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            _generate_oncall_schedule(),
            [],
        ),
        # no oncall schedule matched
        (
            _generate_splunk_schedule(
                rotations=[_generate_splunk_schedule_rotation()],
                overrides=[_generate_splunk_schedule_override()],
            ),
            [_generate_oncall_schedule(name="some other random name")],
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            None,
            [],
        ),
        # missing user ID in a shift
        (
            _generate_splunk_schedule(
                rotations=[_generate_splunk_schedule_rotation()],
            ),
            [_generate_oncall_schedule()],
            {
                SPLUNK_USER1_ID: "user1",
            },
            _generate_oncall_schedule(),
            [_generate_rotation_missing_user_error_msg(SPLUNK_USER2_ID)],
        ),
        # override with a missing user ID
        (
            _generate_splunk_schedule(
                rotations=[],
                overrides=[
                    _generate_splunk_schedule_override(
                        override_oncall_user=SPLUNK_USER2_ID
                    )
                ],
            ),
            [_generate_oncall_schedule()],
            {
                SPLUNK_USER1_ID: "user1",
            },
            _generate_oncall_schedule(),
            [_generate_override_missing_user_error_msg(SPLUNK_USER2_ID)],
        ),
    ],
)
def test_match_schedule(
    splunk_schedule,
    oncall_schedules,
    user_id_map,
    expected_oncall_schedule_match,
    expected_errors,
):
    schedules.match_schedule(splunk_schedule, oncall_schedules, user_id_map)
    assert splunk_schedule["oncall_schedule"] == expected_oncall_schedule_match
    assert splunk_schedule["migration_errors"] == expected_errors


@mock.patch("lib.splunk.resources.schedules.OnCallAPIClient")
@pytest.mark.parametrize(
    "splunk_schedule,user_id_map,expected_oncall_schedule_id_to_be_deleted,expected_oncall_shift_create_calls,expected_oncall_schedule_create_call",
    [
        # matched oncall schedule, should be deleted
        # w/ a basic rotation shift and an override
        (
            _generate_splunk_schedule(
                rotations=[_generate_splunk_schedule_rotation()],
                overrides=[_generate_splunk_schedule_override()],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                # rotation on-call shift
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": ROTATION_SHIFT_NAME,
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-23T13:00:00",
                        "start": "2024-04-23T13:00:00",
                        "duration": 604800,
                        "frequency": "weekly",
                        "interval": 1,
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                # override shift
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": mock.ANY,
                        "type": "override",
                        "rotation_start": "2024-05-01T15:00:00",
                        "start": "2024-05-01T15:00:00",
                        "duration": 21600,
                        "users": [ONCALL_USER2_ID],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 2),
        ),
        # schedule w/ one rotation which has two shift layers
        (
            _generate_splunk_schedule(
                rotations=[
                    _generate_splunk_schedule_rotation(
                        shifts=[
                            _generate_full_day_splunk_schedule_rotation_shift(
                                shift_name="shift1",
                                start="2024-04-23T13:00:00Z",
                                duration=7,
                            ),
                            _generate_full_day_splunk_schedule_rotation_shift(
                                shift_name="shift2",
                                start="2024-04-29T13:00:00Z",
                                duration=2,
                            ),
                        ]
                    ),
                ],
                overrides=[_generate_splunk_schedule_override()],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                # 7 day shift
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "shift1",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-23T13:00:00",
                        "start": "2024-04-23T13:00:00",
                        "duration": 604800,
                        "frequency": "weekly",
                        "interval": 1,
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                # 2 day shift in same rotation as shift above
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "shift2",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 172800,
                        "frequency": "daily",
                        "interval": 2,
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                # override shift
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": mock.ANY,
                        "type": "override",
                        "rotation_start": "2024-05-01T15:00:00",
                        "start": "2024-05-01T15:00:00",
                        "duration": 21600,
                        "users": [ONCALL_USER2_ID],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 3),
        ),
        # schedule w/ one rotation which has a partial day shift layer
        (
            _generate_splunk_schedule(
                rotations=[
                    _generate_splunk_schedule_rotation(
                        shifts=[
                            _generate_partial_day_splunk_schedule_rotation_shift(
                                shift_name="shift1",
                                start="2024-04-29T13:00:00Z",
                                mask_off_days=["sa", "su"],
                                mask_start_hour=9,
                                mask_start_minute=30,
                                mask_end_hour=16,
                                mask_end_minute=30,
                            ),
                        ]
                    ),
                ],
                overrides=[_generate_splunk_schedule_override()],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                # monday to friday 9h30 - 16h30 shifts
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "shift1",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 60 * 60 * 7,  # 7 hours
                        "frequency": "daily",
                        "interval": 1,
                        "by_day": ["MO", "TU", "WE", "TH", "FR"],
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": mock.ANY,
                        "type": "override",
                        "rotation_start": "2024-05-01T15:00:00",
                        "start": "2024-05-01T15:00:00",
                        "duration": 21600,
                        "users": [ONCALL_USER2_ID],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 2),
        ),
        # schedule w/ one rotation which has two partial day shift layers
        (
            _generate_splunk_schedule(
                rotations=[
                    _generate_splunk_schedule_rotation(
                        shifts=[
                            _generate_partial_day_splunk_schedule_rotation_shift(
                                shift_name="shift1",
                                start="2024-04-29T13:00:00Z",
                                mask_off_days=["sa", "su"],
                                mask_start_hour=9,
                                mask_start_minute=30,
                                mask_end_hour=16,
                                mask_end_minute=30,
                            ),
                            _generate_partial_day_splunk_schedule_rotation_shift(
                                shift_name="shift2",
                                start="2024-05-01T00:30:00Z",
                                mask_off_days=["m", "t", "f"],
                                mask_start_hour=20,
                                mask_start_minute=30,
                                mask_end_hour=23,
                                mask_end_minute=0,
                            ),
                        ]
                    ),
                ],
                overrides=[_generate_splunk_schedule_override()],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                # monday to friday 9h30 - 16h30 shifts
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "shift1",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 60 * 60 * 7,  # 7 hours
                        "frequency": "daily",
                        "interval": 1,
                        "by_day": ["MO", "TU", "WE", "TH", "FR"],
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                # sun, wed, thurs, sat 20h30 - 23h shifts
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "shift2",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-05-01T00:30:00",
                        "start": "2024-05-01T00:30:00",
                        "duration": int(60 * 60 * 2.5),  # 2.5 hours
                        "frequency": "daily",
                        "interval": 1,
                        "by_day": ["WE", "TH", "SA", "SU"],
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": mock.ANY,
                        "type": "override",
                        "rotation_start": "2024-05-01T15:00:00",
                        "start": "2024-05-01T15:00:00",
                        "duration": 21600,
                        "users": [ONCALL_USER2_ID],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 3),
        ),
        # schedule w/ one rotation which has one partial day rotation w/ handoff every 3 days
        (
            _generate_splunk_schedule(
                rotations=[
                    _generate_splunk_schedule_rotation(
                        shifts=[
                            _generate_partial_day_splunk_schedule_rotation_shift(
                                shift_name="partial day 3 day handoff",
                                start="2024-04-29T13:00:00Z",
                                mask_off_days=["sa", "su"],
                                mask_start_hour=9,
                                mask_start_minute=0,
                                mask_end_hour=17,
                                mask_end_minute=0,
                                duration=3,
                            ),
                        ]
                    ),
                ],
                overrides=[_generate_splunk_schedule_override()],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "partial day 3 day handoff",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 60 * 60 * 8,  # 8 hours
                        "frequency": "daily",
                        "interval": 3,
                        "by_day": ["MO", "TU", "WE", "TH", "FR"],
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": mock.ANY,
                        "type": "override",
                        "rotation_start": "2024-05-01T15:00:00",
                        "start": "2024-05-01T15:00:00",
                        "duration": 21600,
                        "users": [ONCALL_USER2_ID],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 2),
        ),
        # schedule w/ one rotation which has multiple multi-day shifts
        (
            _generate_splunk_schedule(
                rotations=[
                    _generate_splunk_schedule_rotation(
                        shifts=[
                            _generate_multi_day_splunk_schedule_rotation_shift(
                                shift_name="multi day shift1",
                                start="2024-04-29T13:00:00Z",
                                mask=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "th", "f", "sa", "su"],
                                    start_hour=17,
                                    start_minute=0,
                                    end_hour=0,
                                    end_minute=0,
                                ),
                                mask2=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "w", "sa", "su"],
                                    start_hour=0,
                                    start_minute=0,
                                    end_hour=0,
                                    end_minute=0,
                                ),
                                mask3=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "w", "th", "f", "su"],
                                    start_hour=0,
                                    start_minute=0,
                                    end_hour=9,
                                    end_minute=0,
                                ),
                            ),
                            _generate_multi_day_splunk_schedule_rotation_shift(
                                shift_name="multi day shift2",
                                start="2024-04-29T13:00:00Z",
                                mask=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "th", "f", "sa", "su"],
                                    start_hour=17,
                                    start_minute=0,
                                    end_hour=0,
                                    end_minute=0,
                                ),
                                mask2=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "w", "th", "f", "sa", "su"],
                                    start_hour=0,
                                    start_minute=0,
                                    end_hour=0,
                                    end_minute=0,
                                ),
                                mask3=_generate_splunk_schedule_rotation_shift_mask(
                                    off_days=["m", "t", "w", "f", "sa", "su"],
                                    start_hour=0,
                                    start_minute=0,
                                    end_hour=9,
                                    end_minute=0,
                                ),
                            ),
                        ]
                    ),
                ],
                overrides=[],
                oncall_schedule=_generate_oncall_schedule(id=ONCALL_SCHEDULE_ID),
            ),
            DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP,
            ONCALL_SCHEDULE_ID,
            [
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "multi day shift1",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 60 * 60 * 64,  # 8 hours
                        "frequency": "weekly",
                        "interval": 1,
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
                _generate_oncall_shift_create_api_payload(
                    {
                        "name": "multi day shift2",
                        "level": 1,
                        "type": "rolling_users",
                        "rotation_start": "2024-04-29T13:00:00",
                        "start": "2024-04-29T13:00:00",
                        "duration": 60 * 60 * 16,  # 16 hours
                        "frequency": "weekly",
                        "interval": 1,
                        "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                    }
                ),
            ],
            _generate_oncall_schedule_create_api_payload(_generate_schedule_name(), 2),
        ),
    ],
)
def test_migrate_schedule(
    mock_oncall_client,
    splunk_schedule,
    user_id_map,
    expected_oncall_schedule_id_to_be_deleted,
    expected_oncall_shift_create_calls,
    expected_oncall_schedule_create_call,
):
    schedules.migrate_schedule(splunk_schedule, user_id_map)

    if expected_oncall_schedule_id_to_be_deleted is not None:
        mock_oncall_client.delete.assert_called_once_with(
            f"schedules/{expected_oncall_schedule_id_to_be_deleted}"
        )

    expected_oncall_api_create_calls_args = [
        ("on_call_shifts", shift) for shift in expected_oncall_shift_create_calls
    ]
    expected_oncall_api_create_calls_args.append(
        ("schedules", expected_oncall_schedule_create_call)
    )

    for expected_call_args in expected_oncall_api_create_calls_args:
        mock_oncall_client.create.assert_any_call(*expected_call_args)


@pytest.mark.parametrize(
    "rotation_shift_duration_days,is_allowed",
    [
        # handoff every week, allowed
        (7, True),
        # handoff every two weeks, not currently supported
        (14, False),
    ],
)
def test_migrate_schedule_multi_day_shift_with_non_weekly_handoff_not_supported(
    rotation_shift_duration_days, is_allowed
):
    shift_name = "test shift name"
    multi_day_rotation_shift = schedules.RotationShift.from_dict(
        _generate_multi_day_splunk_schedule_rotation_shift(
            shift_name=shift_name,
            start="2024-04-29T13:00:00Z",
            mask=_generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "th", "f", "sa", "su"],
                start_hour=17,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            mask2=_generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            mask3=_generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "th", "f", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=9,
                end_minute=0,
            ),
            duration=rotation_shift_duration_days,
        ),
        1,
    )

    if is_allowed:
        try:
            oncall_shift = multi_day_rotation_shift.to_oncall_shift(
                DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP
            )

            assert oncall_shift == _generate_oncall_shift_create_api_payload(
                {
                    "name": shift_name,
                    "level": 1,
                    "type": "rolling_users",
                    "rotation_start": "2024-04-29T13:00:00",
                    "start": "2024-04-29T13:00:00",
                    "duration": 60 * 60 * 64,  # 64 hours
                    "frequency": "weekly",
                    "interval": 1,
                    "rolling_users": [[ONCALL_USER1_ID], [ONCALL_USER2_ID]],
                }
            )
        except:  # noqa: E722
            pytest.fail(
                f"Multi-day rotation shift with handoff every {rotation_shift_duration_days} days should be allowed"
            )
    else:
        with pytest.raises(ValueError) as e:
            multi_day_rotation_shift.to_oncall_shift(
                DEFAULT_SPLUNK_USERNAME_TO_ONCALL_USER_ID_MAP
            )

        assert (
            str(e.value)
            == f"Multi-day shifts with a duration greater than 7 days are not supported: {rotation_shift_duration_days} days"
        )


@pytest.mark.parametrize(
    "mask,mask2,mask3,expected_duration_seconds",
    [
        # wednesday 17h to saturday 9h
        (
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "th", "f", "sa", "su"],
                start_hour=17,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "th", "f", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=9,
                end_minute=0,
            ),
            60 * 60 * 64,  # 64 hours, in seconds
        ),
        # wednesday 17h to thursday 9h
        (
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "th", "f", "sa", "su"],
                start_hour=17,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "th", "f", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "f", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=9,
                end_minute=0,
            ),
            60 * 60 * 16,  # 16 hours, in seconds
        ),
        # friday 17h to monday 9h
        (
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "th", "sa", "su"],
                start_hour=17,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["m", "t", "w", "th", "f", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=0,
                end_minute=0,
            ),
            _generate_splunk_schedule_rotation_shift_mask(
                off_days=["t", "w", "th", "f", "sa", "su"],
                start_hour=0,
                start_minute=0,
                end_hour=9,
                end_minute=0,
            ),
            60 * 60 * 64,  # 64 hours, in seconds
        ),
    ],
)
def test_calculate_multi_day_duration_from_masks_for_multi_day_rotation_shift(
    mask, mask2, mask3, expected_duration_seconds
):
    rotation_shift = schedules.RotationShift.from_dict(
        _generate_multi_day_splunk_schedule_rotation_shift(
            shift_name="asdfasdf",
            start="2024-04-29T13:00:00Z",
            mask=mask,
            mask2=mask2,
            mask3=mask3,
        ),
        1,
    )

    calculated_duration = rotation_shift._calculate_multi_day_duration_from_masks()
    assert int(calculated_duration.total_seconds()) == expected_duration_seconds
