# NOTE: this is being left in this directory on purpose, it will be moved to apps/alerts/migrations
# in a separate PR/release
#
# Generated by Django 4.2.17 on 2024-12-06 17:05

import django_migration_linter as linter
from django.db import migrations

import common.migrations.remove_field


class Migration(migrations.Migration):
    dependencies = [
        ("slack", "0013_remove_slackmessage__channel_id_db"),
    ]

    operations = [
        linter.IgnoreMigration(),
        common.migrations.remove_field.RemoveFieldDB(
            model_name="SlackMessage",
            name="organization",
            remove_state_migration=("slack", "0012_remove_slackmessage_organization_state"),
        ),
    ]
