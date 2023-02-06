# Generated by Django 3.2.5 on 2022-05-31 14:46

import apps.heartbeat.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_migration_linter as linter


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('alerts', '0001_squashed_initial'),
    ]

    operations = [
        linter.IgnoreMigration(),
        migrations.CreateModel(
            name='IntegrationHeartBeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('timeout_seconds', models.IntegerField(default=0)),
                ('last_heartbeat_time', models.DateTimeField(default=None, null=True)),
                ('last_checkup_task_time', models.DateTimeField(default=None, null=True)),
                ('actual_check_up_task_id', models.CharField(max_length=100)),
                ('previous_alerted_state_was_life', models.BooleanField(default=True)),
                ('public_primary_key', models.CharField(default=apps.heartbeat.models.generate_public_primary_key_for_integration_heart_beat, max_length=20, unique=True, validators=[django.core.validators.MinLengthValidator(13)])),
                ('alert_receive_channel', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='integration_heartbeat', to='alerts.alertreceivechannel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HeartBeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('timeout_seconds', models.IntegerField(default=0)),
                ('last_heartbeat_time', models.DateTimeField(default=None, null=True)),
                ('last_checkup_task_time', models.DateTimeField(default=None, null=True)),
                ('actual_check_up_task_id', models.CharField(max_length=100)),
                ('previous_alerted_state_was_life', models.BooleanField(default=True)),
                ('message', models.TextField(default='')),
                ('title', models.TextField(default='HeartBeat Title')),
                ('link', models.URLField(default=None, max_length=500, null=True)),
                ('user_defined_id', models.CharField(default='default', max_length=100)),
                ('alert_receive_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='heartbeats', to='alerts.alertreceivechannel')),
            ],
            options={
                'unique_together': {('alert_receive_channel', 'user_defined_id')},
            },
        ),
    ]
