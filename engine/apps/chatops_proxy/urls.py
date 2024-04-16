from common.api_helpers.optional_slash_router import optional_slash_path

from .views import ReceiveBroadcast

urlpatterns = [
    optional_slash_path("broadcast", ReceiveBroadcast.as_view()),
]
