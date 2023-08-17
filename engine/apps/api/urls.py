from django.urls import include, path, re_path

from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

from .views import UserNotificationPolicyView, auth
from .views.alert_group import AlertGroupView
from .views.alert_receive_channel import AlertReceiveChannelView
from .views.alert_receive_channel_template import AlertReceiveChannelTemplateView
from .views.alerts import AlertDetailView
from .views.channel_filter import ChannelFilterView
from .views.custom_button import CustomButtonView
from .views.escalation_chain import EscalationChainViewSet
from .views.escalation_policy import EscalationPolicyView
from .views.features import FeaturesAPIView
from .views.integration_heartbeat import IntegrationHeartBeatView
from .views.live_setting import LiveSettingViewSet
from .views.on_call_shifts import OnCallShiftView
from .views.organization import (
    CurrentOrganizationView,
    GetChannelVerificationCode,
    GetTelegramVerificationCode,
    SetGeneralChannel,
)
from .views.paging import DirectPagingAPIView
from .views.preview_template_options import PreviewTemplateOptionsView
from .views.public_api_tokens import PublicApiTokenView
from .views.resolution_note import ResolutionNoteView
from .views.route_regex_debugger import RouteRegexDebuggerView
from .views.schedule import ScheduleView
from .views.shift_swap import ShiftSwapViewSet
from .views.slack_channel import SlackChannelView
from .views.slack_team_settings import (
    AcknowledgeReminderOptionsAPIView,
    SlackTeamSettingsAPIView,
    UnAcknowledgeTimeoutOptionsAPIView,
)
from .views.team import TeamViewSet
from .views.telegram_channels import TelegramChannelViewSet
from .views.user import CurrentUserView, UserView
from .views.user_group import UserGroupViewSet
from .views.webhooks import WebhooksView

app_name = "api-internal"

router = OptionalSlashRouter()
router.register(r"users", UserView, basename="user")
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"alertgroups", AlertGroupView, basename="alertgroup")
router.register(r"notification_policies", UserNotificationPolicyView, basename="notification_policy")
router.register(r"escalation_policies", EscalationPolicyView, basename="escalation_policy")
router.register(r"escalation_chains", EscalationChainViewSet, basename="escalation_chain")
router.register(r"alert_receive_channels", AlertReceiveChannelView, basename="alert_receive_channel")
router.register(
    r"alert_receive_channel_templates", AlertReceiveChannelTemplateView, basename="alert_receive_channel_template"
)
router.register(r"channel_filters", ChannelFilterView, basename="channel_filter")
router.register(r"schedules", ScheduleView, basename="schedule")
router.register(r"custom_buttons", CustomButtonView, basename="custom_button")
router.register(r"webhooks", WebhooksView, basename="webhooks")
router.register(r"resolution_notes", ResolutionNoteView, basename="resolution_note")
router.register(r"telegram_channels", TelegramChannelViewSet, basename="telegram_channel")
router.register(r"slack_channels", SlackChannelView, basename="slack_channel")
router.register(r"user_groups", UserGroupViewSet, basename="user_group")
router.register(r"heartbeats", IntegrationHeartBeatView, basename="integration_heartbeat")
router.register(r"tokens", PublicApiTokenView, basename="api_token")
router.register(r"live_settings", LiveSettingViewSet, basename="live_settings")
router.register(r"oncall_shifts", OnCallShiftView, basename="oncall_shifts")
router.register(r"shift_swaps", ShiftSwapViewSet, basename="shift_swap")

urlpatterns = [
    path("", include(router.urls)),
    optional_slash_path("user", CurrentUserView.as_view(), name="api-user"),
    optional_slash_path("set_general_channel", SetGeneralChannel.as_view(), name="api-set-general-log-channel"),
    optional_slash_path("organization", CurrentOrganizationView.as_view(), name="api-organization"),
    # TODO: remove current_team routes in future release
    optional_slash_path("current_team", CurrentOrganizationView.as_view(), name="api-current-team"),
    optional_slash_path(
        "current_team/get_telegram_verification_code",
        GetTelegramVerificationCode.as_view(),
        name="api-get-telegram-verification-code",
    ),
    optional_slash_path(
        "current_team/get_channel_verification_code",
        GetChannelVerificationCode.as_view(),
        name="api-get-channel-verification-code",
    ),
    optional_slash_path("slack_settings", SlackTeamSettingsAPIView.as_view(), name="slack-settings"),
    optional_slash_path(
        "slack_settings/acknowledge_remind_options",
        AcknowledgeReminderOptionsAPIView.as_view(),
        name="acknowledge-reminder-options",
    ),
    optional_slash_path(
        "slack_settings/unacknowledge_timeout_options",
        UnAcknowledgeTimeoutOptionsAPIView.as_view(),
        name="unacknowledge-timeout-options",
    ),
    optional_slash_path("features", FeaturesAPIView.as_view(), name="features"),
    optional_slash_path(
        "preview_template_options", PreviewTemplateOptionsView.as_view(), name="preview_template_options"
    ),
    optional_slash_path("route_regex_debugger", RouteRegexDebuggerView.as_view(), name="route_regex_debugger"),
    re_path(r"^alerts/(?P<id>\w+)/?$", AlertDetailView.as_view(), name="alerts-detail"),
    optional_slash_path("direct_paging", DirectPagingAPIView.as_view(), name="direct_paging"),
]

urlpatterns += [
    # For some reason frontend is using url without / at the end. Hacking here to avoid 301's :(
    path(r"login/<backend>", auth.overridden_login_slack_auth, name="slack-auth-with-no-slash"),
    path(r"login/<backend>/", auth.overridden_login_slack_auth, name="slack-auth"),
    path(r"complete/<backend>/", auth.overridden_complete_slack_auth, name="complete-slack-auth"),
]
