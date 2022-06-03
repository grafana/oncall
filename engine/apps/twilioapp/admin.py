from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import SMSMessage, TwilioLogRecord


@admin.register(TwilioLogRecord)
class TwilioLogRecordAdmin(CustomModelAdmin):
    list_display = ("id", "user", "phone_number", "type", "status", "succeed", "created_at")
    list_filter = ("created_at", "type", "status", "succeed")


@admin.register(SMSMessage)
class SMSMessageAdmin(CustomModelAdmin):
    list_display = ("id", "receiver", "represents_alert_group", "notification_policy", "created_at")
    list_filter = ("created_at",)
