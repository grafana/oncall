# Generated by Django 4.2.16 on 2024-11-06 21:11

from django.db import migrations
import django_migration_linter as linter


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0065_alertreceivechannel_service_account'),
    ]

    operations = [
        linter.IgnoreMigration(),
        migrations.DeleteModel(
            name='AlertGroupPostmortem',
        ),
    ]
