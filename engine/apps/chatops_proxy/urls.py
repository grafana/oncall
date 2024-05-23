from common.api_helpers.optional_slash_router import optional_slash_path

from .views import ChatopsEventsView

app_name = "chatops-proxy"

urlpatterns = [
    optional_slash_path("events", ChatopsEventsView.as_view(), name="events"),
]
