# Generated by Django 4.2.15 on 2024-10-15 05:17

import apps.mattermost.models.channel
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0022_alter_team_unique_together'),
        ('alerts', '0060_relatedincident'),
    ]

    operations = [
        migrations.CreateModel(
            name='MattermostUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mattermost_user_id', models.CharField(max_length=100)),
                ('username', models.CharField(max_length=100)),
                ('nickname', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mattermost_user_identity', to='user_management.user')),
            ],
        ),
        migrations.CreateModel(
            name='MattermostMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_id', models.CharField(max_length=100)),
                ('channel_id', models.CharField(max_length=100)),
                ('message_type', models.IntegerField(choices=[(0, 'Alert group message'), (1, 'Log message')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('alert_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mattermost_messages', to='alerts.alertgroup')),
            ],
        ),
        migrations.CreateModel(
            name='MattermostChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_primary_key', models.CharField(default=apps.mattermost.models.channel.generate_public_primary_key_for_mattermost_channel, max_length=20, unique=True, validators=[django.core.validators.MinLengthValidator(13)])),
                ('mattermost_team_id', models.CharField(max_length=100)),
                ('channel_id', models.CharField(max_length=100)),
                ('channel_name', models.CharField(default=None, max_length=100)),
                ('display_name', models.CharField(default=None, max_length=100)),
                ('is_default_channel', models.BooleanField(default=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mattermost_channels', to='user_management.organization')),
            ],
            options={
                'unique_together': {('organization', 'channel_id')},
            },
        ),
    ]
