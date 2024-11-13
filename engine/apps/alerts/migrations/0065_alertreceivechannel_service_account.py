# Generated by Django 4.2.15 on 2024-11-12 13:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0027_serviceaccount'),
        ('alerts', '0064_migrate_resolutionnoteslackmessage_slack_channel_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertreceivechannel',
            name='service_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alert_receive_channels', to='user_management.serviceaccount'),
        ),
    ]
