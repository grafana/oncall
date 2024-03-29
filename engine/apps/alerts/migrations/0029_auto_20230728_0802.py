# Generated by Django 3.2.20 on 2023-07-28 08:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0013_alter_organization_acknowledge_remind_timeout'),
        ('alerts', '0028_drop_alertreceivechannel_restricted_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertgroup',
            name='acknowledged_by_user',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_alert_groups', to='user_management.user'),
        ),
        migrations.AlterField(
            model_name='alertgroup',
            name='wiped_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wiped_alert_groups', to='user_management.user'),
        ),
    ]
