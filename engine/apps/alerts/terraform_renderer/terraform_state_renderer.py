from django.utils.text import slugify

from apps.schedules.models import OnCallScheduleCalendar


class TerraformStateRenderer:
    STATE_INTEGRATION_TEMPLATE = "terraform import amixr_integration.{} {}\n"
    STATE_ROUTE_TEMPLATE = "terraform import amixr_route.{} {}\n"
    STATE_ESCALATION_CHAIN_TEMPLATE = "terraform import amixr_escalation_chain.{} {}\n"
    STATE_ESCALATION_TEMPLATE = "terraform import amixr_escalation.{} {}\n"
    STATE_SCHEDULE_TEMPLATE = "terraform import amixr_schedule.{} {}\n"
    STATE_ON_CALL_SHIFT_TEMPLATE = "terraform import amixr_on_call_shift.{} {}\n"

    def __init__(self, organization):
        self.organization = organization
        self.used_names = {}

    def render_state(self):
        result = self.render_state_text()
        if len(result) == 0:
            result += "There is nothing here yet. Check Settings to add integration and come back!"
        return result

    def render_state_text(self):
        result = ""

        result += self.render_escalation_chains_related_states_text()

        integrations_related_states_text = self.render_integrations_related_states_text()
        result += integrations_related_states_text

        schedules_related_states_text = self.render_schedule_related_states_text()
        result += schedules_related_states_text

        return result

    def render_escalation_chains_related_states_text(self):
        result = ""
        escalation_chains = self.organization.escalation_chains.all()
        for escalation_chain in escalation_chains:
            resource_name = self.render_name(escalation_chain, "escalation_chains", "name")
            result += self.STATE_ESCALATION_CHAIN_TEMPLATE.format(resource_name, escalation_chain.public_primary_key)

            result += self.render_escalation_policy_state_text(escalation_chain, resource_name)
        return result

    def render_integrations_related_states_text(self):
        result = ""
        integrations = self.organization.alert_receive_channels.all().order_by("created_at")
        for integration in integrations:
            integration_resource_name = self.render_name(integration, "integrations", "verbal_name")
            result += TerraformStateRenderer.STATE_INTEGRATION_TEMPLATE.format(
                integration_resource_name,
                integration.public_primary_key,
            )
            route_text = self.render_route_state_text(integration, integration_resource_name)
            result += route_text
        return result

    def render_schedule_related_states_text(self):
        result = ""
        ical_schedules = self.organization.oncall_schedules.order_by("pk")
        for schedule in ical_schedules:
            schedule_resource_name = self.render_name(schedule, "schedules", "name")
            result += TerraformStateRenderer.STATE_SCHEDULE_TEMPLATE.format(
                schedule_resource_name,
                schedule.public_primary_key,
            )
            if isinstance(schedule, OnCallScheduleCalendar):
                on_call_shifts_text = self.render_on_call_shift_state_text(schedule)
                result += on_call_shifts_text
        return result

    def render_route_state_text(self, integration, integration_resource_name):
        routes = integration.channel_filters.all()
        result = ""
        for num, route in enumerate(routes, start=1):
            if route.is_default:
                continue
            route_name = f"route-{num}-{integration_resource_name}"
            result += TerraformStateRenderer.STATE_ROUTE_TEMPLATE.format(
                route_name,
                route.public_primary_key,
            )

        return result

    def render_escalation_policy_state_text(self, escalation_chain, escalation_chain_resource_name):
        result = ""
        escalation_policies = escalation_chain.escalation_policies.all()
        for num, escalation_policy in enumerate(escalation_policies, start=1):
            escalation_name = f"escalation-{num}-{escalation_chain_resource_name}"
            result += TerraformStateRenderer.STATE_ESCALATION_TEMPLATE.format(
                escalation_name,
                escalation_policy.public_primary_key,
            )
        return result

    def render_on_call_shift_state_text(self, schedule):
        result = ""
        on_call_shifts = schedule.custom_on_call_shifts.all().order_by("pk")
        for shift in on_call_shifts:
            shift_name = self.render_name(shift, "on_call_shifts", "name")
            result += TerraformStateRenderer.STATE_ON_CALL_SHIFT_TEMPLATE.format(
                shift_name,
                shift.public_primary_key,
            )
        return result

    def render_name(self, obj, obj_verbal, name_attr):
        obj_name = slugify(getattr(obj, name_attr))
        obj_data_name = obj_name
        counter = 1
        while (
            obj_data_name in self.used_names.setdefault(obj_verbal, {})
            and self.used_names[obj_verbal][obj_data_name] != obj.pk
        ):
            counter += 1
            obj_data_name = f"{obj_name}-{counter}"
        self.used_names[obj_verbal][obj_data_name] = obj.pk
        return obj_data_name
