# Generated by Django 3.2.5 on 2022-05-31 14:46

import apps.telegram.models.connectors.channel
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0001_squashed_initial'),
        ('alerts', '0001_squashed_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramVerificationCode',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_verification_code', to='user_management.user')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramToOrganizationConnector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_primary_key', models.CharField(default=apps.telegram.models.connectors.channel.generate_public_primary_key_for_telegram_to_at_connector, max_length=20, unique=True, validators=[django.core.validators.MinLengthValidator(13)])),
                ('is_default_channel', models.BooleanField(default=False, null=True)),
                ('channel_chat_id', models.CharField(max_length=100, unique=True)),
                ('channel_name', models.CharField(default=None, max_length=100, null=True)),
                ('discussion_group_chat_id', models.CharField(max_length=100, unique=True)),
                ('discussion_group_name', models.CharField(default=None, max_length=100, null=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_channel', to='user_management.organization')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.IntegerField()),
                ('chat_id', models.CharField(max_length=100)),
                ('message_type', models.IntegerField(choices=[(0, 'Alert group message'), (1, 'Actions message'), (2, 'Log message'), (3, 'Alert can not be rendered'), (4, 'Alert group message with action buttons and incident log'), (5, 'Link to channel message'), (6, 'Link to channel message without title')])),
                ('discussion_group_message_id', models.IntegerField(default=None, null=True)),
                ('edit_task_id', models.CharField(default=None, max_length=100, null=True)),
                ('alert_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_messages', to='alerts.alertgroup')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramChannelVerificationCode',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='user_management.user')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_verification_code', to='user_management.organization')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramToUserConnector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_chat_id', models.BigIntegerField()),
                ('telegram_nick_name', models.CharField(default=None, max_length=100, null=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_connection', to='user_management.user')),
            ],
            options={
                'unique_together': {('user', 'telegram_chat_id')},
            },
        ),
    ]
