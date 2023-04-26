import datetime

import pytest

from apps.alerts.models import EscalationPolicy
from apps.schedules.models import OnCallScheduleCalendar


@pytest.mark.django_db
def test_copy_escalation_chain(
    make_organization_and_user, make_escalation_chain, make_escalation_policy, make_schedule
):
    organization, user = make_organization_and_user()
    escalation_chain = make_escalation_chain(organization)

    notify_to_multiple_users_step = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    notify_to_multiple_users_step.notify_to_users_queue.set([user])
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )
    # random time for test
    from_time = datetime.time(10, 30)
    to_time = datetime.time(18, 45)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_TIME,
        from_time=from_time,
        to_time=to_time,
    )

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=schedule,
    )
    all_fields = EscalationPolicy._meta.fields  # Note that m-t-m fields are in this list
    fields_to_not_compare = ["id", "public_primary_key", "escalation_chain", "last_notified_user"]
    fields_to_compare = list(map(lambda f: f.name, filter(lambda f: f.name not in fields_to_not_compare, all_fields)))
    copied_chain = escalation_chain.make_copy(f"copy_{escalation_chain.name}", None)
    for policy_from_original, policy_from_copy in zip(
        escalation_chain.escalation_policies.all(), copied_chain.escalation_policies.all()
    ):
        for field in fields_to_compare:
            assert getattr(policy_from_original, field) == getattr(policy_from_copy, field)

        # compare m-t-m fields separately
        assert list(policy_from_original.notify_to_users_queue.all()) == list(
            policy_from_copy.notify_to_users_queue.all()
        )
