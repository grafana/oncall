from apps.email.inbound import InboundEmailWebhookView
from common.api_helpers.optional_slash_router import optional_slash_path

app_name = "email"

urlpatterns = [
    optional_slash_path("inbound", InboundEmailWebhookView.as_view(), name="inbound"),
]
