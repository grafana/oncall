# Generated by Django 4.2.17 on 2024-12-06 17:05

import common.migrations.remove_field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('slack', '0010_remove_slackmessage_active_update_task_id_db'),
    ]

    operations = [
        common.migrations.remove_field.RemoveFieldState(
            model_name='SlackMessage',
            name='_channel_id',
        ),
    ]