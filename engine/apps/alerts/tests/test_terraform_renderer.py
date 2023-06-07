import pytest
from django.utils import timezone
from django.utils.text import slugify

from apps.alerts.models import EscalationPolicy
from apps.alerts.terraform_renderer import TerraformFileRenderer, TerraformStateRenderer
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar

terraform_file_renderer_data = {
    "filtering_term": "\\[test\\]",
    "escaped_filtering_term": "\\\\[test\\\\]",
}

rendered_terraform_file_template = """
data "amixr_user" "{user_name}" {{
    username = "{user_name}"
}}

resource "amixr_escalation_chain" "{escalation_chain_name}" {{
    name = "{escalation_chain_name}"
    team_id = null
}}

resource "amixr_escalation" "escalation-1-{escalation_chain_name}" {{
    escalation_chain_id = amixr_escalation_chain.{escalation_chain_name}.id
    type = "notify_persons"
    important = false
    persons_to_notify = [
        data.amixr_user.{user_name}.id
    ]
    position = 0
}}

resource "amixr_integration" "{integration_name}" {{
    name = "{integration_verbal_name}"
    type = "grafana"
    team_id = null
}}

resource "amixr_on_call_shift" "{shift_name}" {{
    name = "{shift_name}"
    type = "rolling_users"
    team_id = null
    start = "2021-08-16T17:00:00"
    duration = 3600
    level = 0
    frequency = "weekly"
    interval = 1
    week_start = "MO"
    by_day = ["MO", "SA"]
    by_month = null
    by_monthday = null
    rolling_users = [
        [data.amixr_user.{user_name}.id],
    ]
}}

resource "amixr_schedule" "{schedule_name}" {{
    name = "{schedule_name}"
    type = "calendar"
    team_id = null
    time_zone = "UTC"
}}
"""

rendered_terraform_imports_template = """terraform import amixr_escalation_chain.{escalation_chain_name} {escalation_chain_public_primary_key}
terraform import amixr_escalation.escalation-1-{escalation_chain_name} {escalation_1_public_primary_key}
terraform import amixr_integration.{integration_name} {integration_public_primary_key}
"""


@pytest.mark.django_db
def test_render_terraform_file(
    make_organization_and_user_with_slack_identities,
    make_integration_escalation_chain_route_escalation_policy,
    make_escalation_chain,
    make_escalation_policy,
    make_on_call_shift,
    make_schedule,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    (integration, escalation_chain, _, escalation_policy) = make_integration_escalation_chain_route_escalation_policy(
        organization,
        EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    escalation_policy.notify_to_users_queue.add(user)

    schedule = make_schedule(
        organization=organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_calendar_schedule",
    )

    start = timezone.datetime.fromisoformat("2021-08-16T17:00:00Z")

    shift = make_on_call_shift(
        organization=organization,
        name="test_shift",
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        interval=1,
        week_start=CustomOnCallShift.MONDAY,
        start=start,
        rotation_start=start,
        duration=timezone.timedelta(seconds=3600),
        by_day=["MO", "SA"],
        rolling_users=[{user.pk: user.public_primary_key}],
    )

    renderer = TerraformFileRenderer(organization)
    result = renderer.render_terraform_file()

    expected_result = rendered_terraform_file_template.format(
        user_name=slugify(user.username),
        escalation_chain_name=escalation_chain.name,
        integration_name=slugify(integration.verbal_name),
        integration_verbal_name=integration.verbal_name,
        routing_regex=terraform_file_renderer_data["escaped_filtering_term"],
        schedule_name=schedule.name,
        shift_name=shift.name,
    )

    assert result == expected_result


@pytest.mark.django_db
def test_render_terraform_imports(
    make_organization_and_user_with_slack_identities,
    make_integration_escalation_chain_route_escalation_policy,
    make_escalation_chain,
    make_escalation_policy,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    integration, escalation_chain, _, escalation_policy = make_integration_escalation_chain_route_escalation_policy(
        organization,
        EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )

    renderer = TerraformStateRenderer(organization)
    result = renderer.render_state()

    expected_result = rendered_terraform_imports_template.format(
        escalation_chain_name=slugify(escalation_chain.name),
        escalation_chain_public_primary_key=escalation_chain.public_primary_key,
        integration_name=slugify(integration.verbal_name),
        integration_public_primary_key=integration.public_primary_key,
        escalation_1_public_primary_key=escalation_policy.public_primary_key,
    )

    assert result == expected_result
