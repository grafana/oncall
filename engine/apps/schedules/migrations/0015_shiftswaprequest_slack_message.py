# Generated by Django 3.2.20 on 2023-07-26 07:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('slack', '0003_delete_slackactionrecord'),
        ('schedules', '0014_shiftswaprequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftswaprequest',
            name='slack_message',
            field=models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shift_swap_request', to='slack.slackmessage'),
        ),
    ]
