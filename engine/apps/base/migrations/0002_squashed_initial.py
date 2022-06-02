# Generated by Django 3.2.5 on 2022-05-31 14:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0001_squashed_initial'),
        ('base', '0001_squashed_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernotificationpolicylogrecord',
            name='author',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personal_log_records', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='usernotificationpolicylogrecord',
            name='notification_policy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personal_log_records', to='base.usernotificationpolicy'),
        ),
        migrations.AddField(
            model_name='usernotificationpolicy',
            name='user',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_policies', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='organizationlogrecord',
            name='author',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_log_records', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='organizationlogrecord',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_records', to='user_management.organization'),
        ),
        migrations.AddConstraint(
            model_name='dynamicsetting',
            constraint=models.UniqueConstraint(fields=('name',), name='unique_dynamic_setting_name'),
        ),
    ]
