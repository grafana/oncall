from common.api_helpers.optional_slash_router import optional_slash_path

from .views import CloudHeartbeatStatusView

urlpatterns = [
    optional_slash_path("cloud_heartbeat_status", CloudHeartbeatStatusView.as_view(), name="cloud_heartbeat_status"),
]
