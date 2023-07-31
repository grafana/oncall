from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import SlackMessage, SlackTeamIdentity, SlackUserIdentity


@admin.register(SlackTeamIdentity)
class SlackTeamIdentityAdmin(CustomModelAdmin):
    list_display = ("id", "slack_id", "cached_name", "datetime")
    list_filter = ("datetime",)


@admin.register(SlackUserIdentity)
class SlackUserIdentityAdmin(CustomModelAdmin):
    list_display = ("id", "slack_id", "slack_team_identity", "cached_name", "cached_slack_email")

    def get_queryset(self, request):
        return SlackUserIdentity.all_objects


@admin.register(SlackMessage)
class SlackMessageAdmin(CustomModelAdmin):
    list_display = ("id", "slack_id", "_slack_team_identity", "alert_group", "created_at")
    list_filter = ("created_at",)
