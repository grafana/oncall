# Generated by Django 4.2.16 on 2024-11-20 20:23

import common.migrations.remove_field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0067_remove_channelfilter__slack_channel_id_state'),
    ]

    operations = [
        common.migrations.remove_field.RemoveFieldState(
            model_name='resolutionnoteslackmessage',
            name='_slack_channel_id',
        ),
    ]
