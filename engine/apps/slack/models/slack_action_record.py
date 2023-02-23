from django.db import models

# from apps.slack.scenarios.scenario_step import ScenarioStep


class SlackActionRecord(models.Model):
    """
    Legacy model, should be removed.
    """

    ON_CALL_ROUTINE = [
        # ScenarioStep.get_step("distribute_alerts", "CustomButtonProcessStep").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep").routing_uid(),
        # ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep").routing_uid(),
    ]

    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="actions")

    user = models.ForeignKey(
        "user_management.User", on_delete=models.SET_NULL, null=True, default=None, related_name="actions"
    )

    step = models.CharField(max_length=100, null=True, default=None)
    payload = models.TextField(null=True, default=None)
    datetime = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def filter_only_incident_routine(queryset):
        return queryset.filter(step__in=SlackActionRecord.ON_CALL_ROUTINE)
