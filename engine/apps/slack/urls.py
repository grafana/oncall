from django.urls import path

from .views import (
    InstallLinkRedirectView,
    OAuthSlackView,
    ResetSlackView,
    SignupRedirectView,
    SlackEventApiEndpointView,
)

urlpatterns = [
    path("event_api_endpoint/", SlackEventApiEndpointView.as_view()),
    path("interactive_api_endpoint/", SlackEventApiEndpointView.as_view()),
    path("oauth/", OAuthSlackView.as_view()),
    path("oauth/<str:subscription>/<str:utm>/", OAuthSlackView.as_view()),
    path("install_redirect/", InstallLinkRedirectView.as_view()),
    path("install_redirect/<str:subscription>/<str:utm>/", InstallLinkRedirectView.as_view()),
    path("signup_redirect/", SignupRedirectView.as_view()),
    path("signup_redirect/<str:subscription>/<str:utm>/", SignupRedirectView.as_view()),
    # Trailing / is missing here on purpose. QA the feature if you want to add it. No idea why doesn't it work with it.
    path("reset_slack", ResetSlackView.as_view(), name="reset-slack"),
]
