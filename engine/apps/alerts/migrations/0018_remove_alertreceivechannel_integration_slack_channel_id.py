# Generated by Django 3.2.19 on 2023-06-28 16:00

from django.db import migrations
import django_migration_linter as linter


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0017_alertgroup_is_restricted'),
    ]

    operations = [
        linter.IgnoreMigration(),  # This field is deprecated a long time ago.
        migrations.RemoveField(
            model_name='alertreceivechannel',
            name='integration_slack_channel_id',
        ),
    ]
