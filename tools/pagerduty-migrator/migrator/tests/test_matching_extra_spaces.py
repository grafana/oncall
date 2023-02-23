from migrator.resources.escalation_policies import match_escalation_policy
from migrator.resources.integrations import match_integration
from migrator.resources.schedules import match_schedule


def test_match_schedule_name_extra_spaces():
    pd_schedule = {"name": " test "}
    oncall_schedules = [{"name": "test"}]

    match_schedule(pd_schedule, oncall_schedules, user_id_map={})
    assert pd_schedule["oncall_schedule"] == oncall_schedules[0]


def test_match_escalation_policy_name_extra_spaces():
    pd_escalation_policy = {"name": " test "}
    oncall_escalation_chains = [{"name": "test"}]

    match_escalation_policy(pd_escalation_policy, oncall_escalation_chains)
    assert (
        pd_escalation_policy["oncall_escalation_chain"] == oncall_escalation_chains[0]
    )


def test_match_integration_name_extra_spaces():
    pd_integration = {
        "service": {"name": " test service "},
        "name": " test integration ",
    }
    oncall_integrations = [{"name": "test service  -  test integration"}]

    match_integration(pd_integration, oncall_integrations)
    assert pd_integration["oncall_integration"] == oncall_integrations[0]
