from django.urls import path

from .views import WebHookView

urlpatterns = [
    path("", WebHookView.as_view()),
]
