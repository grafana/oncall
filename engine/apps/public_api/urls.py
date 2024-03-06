from django.urls import include, path

from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

from . import views

app_name = "api-public"


router = OptionalSlashRouter()

router.register(r"organizations", views.OrganizationView, basename="organizations")
router.register(r"users", views.UserView, basename="users")
router.register(r"integrations", views.IntegrationView, basename="integrations")
router.register(r"routes", views.ChannelFilterView, basename="routes")
router.register(r"schedules", views.OnCallScheduleChannelView, basename="schedules")
router.register(r"escalation_chains", views.EscalationChainView, basename="escalation_chains")
router.register(r"escalation_policies", views.EscalationPolicyView, basename="escalation_policies")
router.register(r"alerts", views.AlertView, basename="alerts")
router.register(r"alert_groups", views.IncidentView, basename="alert_groups")
router.register(r"slack_channels", views.SlackChannelView, basename="slack_channels")
router.register(r"personal_notification_rules", views.PersonalNotificationView, basename="personal_notification_rules")
router.register(r"resolution_notes", views.ResolutionNoteView, basename="resolution_notes")
router.register(r"actions", views.ActionView, basename="actions")
router.register(r"user_groups", views.UserGroupView, basename="user_groups")
router.register(r"on_call_shifts", views.CustomOnCallShiftView, basename="on_call_shifts")
router.register(r"teams", views.TeamView, basename="teams")
router.register(r"shift_swaps", views.ShiftSwapViewSet, basename="shift_swap")
router.register(r"webhooks", views.WebhooksView, basename="webhooks")


urlpatterns = [
    path("", include(router.urls)),
    optional_slash_path("info", views.InfoView.as_view(), name="info"),
    optional_slash_path("make_call", views.MakeCallView.as_view(), name="make_call"),
    optional_slash_path("send_sms", views.SendSMSView.as_view(), name="send_sms"),
]
