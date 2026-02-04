# Generated migration for Zoom integration

import apps.zoom.models.channel
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0026_auto_20241017_1919'),
        ('alerts', '0001_squashed_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZoomChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_primary_key', models.CharField(
                    default=apps.zoom.models.channel.generate_public_primary_key_for_zoom_channel,
                    max_length=20,
                    unique=True,
                    validators=[django.core.validators.MinLengthValidator(13)]
                )),
                ('channel_id', models.CharField(max_length=100)),
                ('channel_name', models.CharField(default=None, max_length=255)),
                ('is_default_channel', models.BooleanField(default=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zoom_channels',
                    to='user_management.organization'
                )),
            ],
        ),
        migrations.CreateModel(
            name='ZoomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zoom_user_id', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=255)),
                ('display_name', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zoom_user_identity',
                    to='user_management.user'
                )),
            ],
            options={
                'indexes': [models.Index(fields=['zoom_user_id'], name='zoom_zoomus_zoom_us_idx')],
            },
        ),
        migrations.CreateModel(
            name='ZoomMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(max_length=100)),
                ('channel_id', models.CharField(max_length=100)),
                ('message_type', models.IntegerField(choices=[(0, 'Alert group message'), (1, 'Log message')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('alert_group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zoom_messages',
                    to='alerts.alertgroup'
                )),
            ],
            options={
                'indexes': [models.Index(fields=['channel_id', 'message_id'], name='zoom_zoomme_channel_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='zoommessage',
            constraint=models.UniqueConstraint(
                fields=('alert_group', 'message_type', 'channel_id'),
                name='unique_zoom_alert_group_message_type_channel_id'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='zoomchannel',
            unique_together={('organization', 'channel_id')},
        ),
    ]
