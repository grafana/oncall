from django.urls import path

from .views import GetMattermostManifest, MattermostBindings, MattermostInstall

app_name = "mattermost"

urlpatterns = [
    path("manifest", GetMattermostManifest.as_view(), name="manifest"),
    path("install", MattermostInstall.as_view(), name="install"),
    path("bindings", MattermostBindings.as_view(), name="bindings"),
]
