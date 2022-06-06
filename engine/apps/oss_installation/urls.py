from django.urls import path

from common.api_helpers.optional_slash_router import optional_slash_path

from .views import CloudConnectionView, CloudUsersView, CloudUserView

urlpatterns = [
    optional_slash_path("cloud_users", CloudUsersView.as_view(), name="cloud-users-list"),
    path(
        "cloud_users/<str:pk>",
        CloudUserView.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="cloud-user-detail",
    ),
    optional_slash_path("cloud_connection", CloudConnectionView.as_view(), name="cloud-connection-status"),
]
