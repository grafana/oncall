from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import (
    Alert,
    AlertGroup,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    ChannelFilter,
    CustomButton,
    EscalationChain,
    EscalationPolicy,
    Invitation,
)


@admin.register(Alert)
class AlertAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "group", "title", "created_at")
    list_filter = ("created_at",)


@admin.register(AlertGroup)
class AlertGroupAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "web_title_cache", "channel", "channel_filter", "state", "started_at")
    list_filter = ("started_at",)

    def get_queryset(self, request):
        return AlertGroup.objects


@admin.register(AlertGroupLogRecord)
class AlertGroupLogRecord(CustomModelAdmin):
    list_display = ("id", "alert_group", "escalation_policy", "type", "created_at")
    list_filter = ("created_at", "type")


@admin.register(AlertReceiveChannel)
class AlertReceiveChannelAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "integration", "token", "created_at", "deleted_at")
    list_filter = ("integration",)

    def get_queryset(self, request):
        return AlertReceiveChannel.objects_with_deleted


@admin.register(ChannelFilter)
class ChannelFilterAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "alert_receive_channel", "escalation_chain", "filtering_term", "order")


@admin.register(CustomButton)
class CustomButtonModelAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "name", "webhook")


@admin.register(EscalationChain)
class EscalationChainAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "organization", "name")


@admin.register(EscalationPolicy)
class EscalationPolicyAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "escalation_chain", "step_type_verbal", "order")


@admin.register(Invitation)
class InvitationAdmin(CustomModelAdmin):
    list_display = ("id", "alert_group", "author", "invitee", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
