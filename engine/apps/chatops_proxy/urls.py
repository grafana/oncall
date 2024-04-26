from common.api_helpers.optional_slash_router import optional_slash_path

from .views import ChatopsEvents

urlpatterns = [
    optional_slash_path("events", ChatopsEvents.as_view()),
]
