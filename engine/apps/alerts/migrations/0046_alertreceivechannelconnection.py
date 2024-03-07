# Generated by Django 4.2.10 on 2024-03-07 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0045_escalationpolicy_notify_to_team_members_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertReceiveChannelConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backsync', models.BooleanField(default=False)),
                ('connected_alert_receive_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_alert_receive_channels', to='alerts.alertreceivechannel')),
                ('source_alert_receive_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connected_alert_receive_channels', to='alerts.alertreceivechannel')),
            ],
            options={
                'unique_together': {('source_alert_receive_channel', 'connected_alert_receive_channel')},
            },
        ),
    ]
