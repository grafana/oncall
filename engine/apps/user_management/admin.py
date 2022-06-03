from django.contrib import admin

from common.admin import CustomModelAdmin

from .models import Organization, Team, User


@admin.register(User)
class UserAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "organization", "username", "email")


@admin.register(Team)
class TeamAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "organization", "name")


@admin.register(Organization)
class OrganizationAdmin(CustomModelAdmin):
    list_display = ("id", "public_primary_key", "org_title", "org_slug", "org_id", "stack_id")
