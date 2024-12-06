# NOTE: this is being left in this directory on purpose, it will be moved to apps/alerts/migrations
# in a separate PR/release
#
# Generated by Django 4.2.17 on 2024-12-06 17:05

import common.migrations.remove_field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('slack', '0012_remove_slackmessage_organization_state'),
    ]

    operations = [
        common.migrations.remove_field.RemoveFieldDB(
            model_name='SlackMessage',
            name='_channel_id',
            remove_state_migration=('slack', '0011_remove_slackmessage__channel_id_state'),
        ),
    ]
