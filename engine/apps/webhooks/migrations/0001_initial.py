# Generated by Django 3.2.16 on 2022-12-05 19:09

import apps.webhooks.models.webhooks
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import mirage.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0005_rbac_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_primary_key', models.CharField(default=apps.webhooks.models.webhooks.generate_public_primary_key_for_webhook, max_length=20, unique=True, validators=[django.core.validators.MinLengthValidator(13)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('username', models.CharField(default=None, max_length=100, null=True)),
                ('password', mirage.fields.EncryptedCharField(default=None, max_length=200, null=True)),
                ('authorization_header', models.CharField(default=None, max_length=1000, null=True)),
                ('trigger_template', models.TextField(default=None, null=True)),
                ('headers', models.JSONField(default=dict)),
                ('headers_template', models.TextField(default=None, null=True)),
                ('url', models.CharField(default=None, max_length=1000, null=True)),
                ('url_template', models.TextField(default=None, null=True)),
                ('data', models.TextField(default=None, null=True)),
                ('forward_all', models.BooleanField(default=True)),
                ('http_method', models.CharField(default='POST', max_length=32)),
                ('trigger_type', models.IntegerField(choices=[(0, 'As escalation step'), (1, 'As user notification step'), (2, 'Alert group acknowledge'), (3, 'Alert group resolve'), (4, 'Alert group silence')], default=None, null=True)),
                ('organization', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='user_management.organization')),
                ('team', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='user_management.team')),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='user_management.user')),
            ],
        ),
    ]
