from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import DynamicSetting, FailedToInvokeCeleryTask, UserNotificationPolicy, UserNotificationPolicyLogRecord

admin.site.register(DynamicSetting)


@admin.register(UserNotificationPolicy)
class UserNotificationPolicyAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "user", "important", "short_verbal")


@admin.register(UserNotificationPolicyLogRecord)
class UserNotificationPolicyLogRecordAdmin(CustomModelAdmin):
    list_display = ("id", "alert_group", "notification_policy", "author", "type", "created_at")
    list_filter = ("type", "created_at")


@admin.register(FailedToInvokeCeleryTask)
class FailedToInvokeCeleryTaskAdmin(CustomModelAdmin):
    list_display = ("id", "name", "is_sent")
    list_filter = ("is_sent",)
