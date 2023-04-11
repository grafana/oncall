from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import Webhook


@admin.register(Webhook)
class WebhookAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "organization", "name", "url")
