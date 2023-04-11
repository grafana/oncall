from migrator.resources.escalation_policies import match_escalation_policy
from migrator.resources.integrations import match_integration
from migrator.resources.schedules import match_schedule
from migrator.resources.users import match_user


def test_match_user_email_case_insensitive():
    pd_user = {"email": "test@test.com"}
    oncall_users = [{"email": "TEST@TEST.COM"}]

    match_user(pd_user, oncall_users)
    assert pd_user["oncall_user"] == oncall_users[0]


def test_match_schedule_name_case_insensitive():
    pd_schedule = {"name": "Test"}
    oncall_schedules = [{"name": "test"}]

    match_schedule(pd_schedule, oncall_schedules, user_id_map={})
    assert pd_schedule["oncall_schedule"] == oncall_schedules[0]


def test_match_escalation_policy_name_case_insensitive():
    pd_escalation_policy = {"name": "Test"}
    oncall_escalation_chains = [{"name": "test"}]

    match_escalation_policy(pd_escalation_policy, oncall_escalation_chains)
    assert (
        pd_escalation_policy["oncall_escalation_chain"] == oncall_escalation_chains[0]
    )


def test_match_integration_name_case_insensitive():
    pd_integration = {"service": {"name": "Test service"}, "name": "test Integration"}
    oncall_integrations = [{"name": "test Service - Test integration"}]

    match_integration(pd_integration, oncall_integrations)
    assert pd_integration["oncall_integration"] == oncall_integrations[0]
