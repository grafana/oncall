from django.urls import path

from .views.channels import ChannelView

urlpatterns = [
    path("channels", ChannelView.as_view()),
]
