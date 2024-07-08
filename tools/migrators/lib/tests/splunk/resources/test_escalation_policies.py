import typing
from unittest import mock

import pytest

from lib.splunk.resources import escalation_policies


def _create_escalation_policy_step_entry(execution_type, data):
    return {
        "executionType": execution_type,
        **data,
    }


def _create_user_execution_type_entry(username):
    return _create_escalation_policy_step_entry(
        "user",
        {
            "user": {
                "username": username,
            },
        },
    )


def _create_oncall_escalation_chain(id: typing.Optional[str]):
    return {
        "id": id,
    }


def _create_escalation_policy(
    team_slug,
    entries,
    name="my escalation policy",
    timeout=0,
    oncall_escalation_chain_id=None,
    other_data=None,
):
    return {
        "name": name,
        "slug": team_slug,
        "steps": [
            {
                "timeout": timeout,
                "entries": entries,
            }
        ],
        "oncall_escalation_chain": _create_oncall_escalation_chain(
            oncall_escalation_chain_id
        )
        if oncall_escalation_chain_id is not None
        else None,
        **(other_data or {}),
    }


def _generate_oncall_escalation_policy_create_api_payload(
    type, escalation_chain_id, data
):
    return {"escalation_chain_id": escalation_chain_id, "type": type, **data}


def _generate_oncall_notify_persons_escalation_policy_create_api_payload(
    escalation_chain_id, persons_to_notify
):
    return _generate_oncall_escalation_policy_create_api_payload(
        "notify_persons",
        1,
        {
            "persons_to_notify": persons_to_notify,
        },
    )


@pytest.mark.parametrize(
    "oncall_escalation_chains,expected",
    [
        ([], None),
        (
            [
                {
                    "id": 1,
                    "name": "foo",
                },
            ],
            {
                "id": 1,
                "name": "foo",
            },
        ),
    ],
)
def test_match_escalation_policy(oncall_escalation_chains, expected):
    policy = {"name": " FOO "}

    escalation_policies.match_escalation_policy(policy, oncall_escalation_chains)
    assert policy["oncall_escalation_chain"] == expected


def test_match_users_and_schedules_for_escalation_policy_unmatched_users():
    policy = _create_escalation_policy(
        "asdfasdf",
        [
            _create_user_execution_type_entry("foo"),
        ],
    )
    users = [
        {
            "username": "foo",
            "oncall_user": {
                "id": 1,
            },
        },
        {"username": "bar", "oncall_user": None},
    ]

    escalation_policies.match_users_and_schedules_for_escalation_policy(
        policy, users, []
    )
    assert policy["unmatched_users"] == []

    policy = _create_escalation_policy(
        "asdasdf",
        [
            _create_user_execution_type_entry("foo"),
            _create_user_execution_type_entry("bar"),
        ],
    )

    escalation_policies.match_users_and_schedules_for_escalation_policy(
        policy, users, []
    )
    assert policy["unmatched_users"] == [{"username": "bar", "oncall_user": None}]


@pytest.mark.parametrize(
    "execution_type,supported",
    [
        ("rotation_group", True),
        ("user", True),
        ("email", False),
        ("webhook", False),
        ("policy_routing", False),
        ("rotation_group_next", False),
        ("rotation_group_previous", False),
        ("team_page", False),
    ],
)
def test_test_match_users_and_schedules_for_escalation_policy_unsupported_escalation_entry_types(
    execution_type, supported
):
    policy = _create_escalation_policy(
        "asdfasdf",
        [
            _create_escalation_policy_step_entry(
                execution_type, {"user": {"username": "foo"}}
            ),
        ],
    )

    escalation_policies.match_users_and_schedules_for_escalation_policy(policy, [], [])
    assert (
        policy["unsupported_escalation_entry_types"] == []
        if supported
        else [execution_type]
    )


def test_match_users_and_schedules_for_escalation_policy_flawed_schedules():
    flawed_schedule_team_slug = "zxcvzxcv"
    flawed_schedule = {
        "team": {
            "slug": flawed_schedule_team_slug,
        },
        "migration_errors": ["blahblahblah"],
    }

    policy = _create_escalation_policy(
        flawed_schedule_team_slug,
        [
            _create_escalation_policy_step_entry("rotation_group", {}),
        ],
    )
    schedules = [
        {
            "team": {
                "slug": "asdfasdf",
            },
            "migration_errors": False,
        },
        {
            "team": {
                "slug": "qwerqwer",
            },
            "migration_errors": False,
        },
        flawed_schedule,
    ]

    escalation_policies.match_users_and_schedules_for_escalation_policy(
        policy, [], schedules
    )
    assert policy["flawed_schedules"] == [flawed_schedule]


@pytest.mark.parametrize(
    "policy,delete_called,expected_oncall_escalation_policy_create_calls",
    [
        (
            _create_escalation_policy(
                "asdfasdf",
                [
                    _create_user_execution_type_entry("foo"),
                ],
                name="hello",
            ),
            False,
            [
                _generate_oncall_notify_persons_escalation_policy_create_api_payload(
                    1, [1]
                )
            ],
        ),
        (
            _create_escalation_policy(
                "asdfasdf",
                [
                    _create_user_execution_type_entry("foo"),
                ],
                name="hello",
                oncall_escalation_chain_id="1234",
            ),
            True,
            [
                _generate_oncall_notify_persons_escalation_policy_create_api_payload(
                    1, [1]
                )
            ],
        ),
    ],
)
@mock.patch("lib.splunk.resources.escalation_policies.OnCallAPIClient")
def test_migrate_escalation_policy(
    mock_oncall_client,
    policy,
    delete_called,
    expected_oncall_escalation_policy_create_calls,
):
    mock_oncall_client.create.return_value = {"id": 1}

    users = [
        {
            "username": "foo",
            "oncall_user": {
                "id": 1,
            },
        },
    ]
    schedules = []

    escalation_policies.migrate_escalation_policy(policy, users, schedules)

    assert policy["oncall_escalation_chain"] == {"id": 1}

    if delete_called:
        mock_oncall_client.delete.assert_called_once_with("escalation_chains/1234")
    else:
        mock_oncall_client.delete.assert_not_called()

    expected_oncall_api_create_calls_args = [
        ("escalation_policies", policy)
        for policy in expected_oncall_escalation_policy_create_calls
    ]
    expected_oncall_api_create_calls_args.append(
        ("escalation_chains", {"name": "hello", "team_id": None})
    )

    for expected_call_args in expected_oncall_api_create_calls_args:
        mock_oncall_client.create.assert_any_call(*expected_call_args)
