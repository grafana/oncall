from django.urls import path

from .views import overridden_complete_slack_auth, overridden_login_slack_auth

app_name = "social_auth"

urlpatterns = [
    path(r"login/<backend>", overridden_login_slack_auth, name="slack-auth-with-no-slash"),
    path(r"login/<backend>/", overridden_login_slack_auth, name="slack-auth"),
    path(r"complete/<backend>/", overridden_complete_slack_auth, name="complete-slack-auth"),
]
