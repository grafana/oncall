from django.contrib import admin

from apps.schedules.models import OnCallSchedule
from common.admin import CustomModelAdmin


@admin.register(OnCallSchedule)
class OnCallScheduleAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "name")
