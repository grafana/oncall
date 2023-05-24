# Generated by Django 3.2.18 on 2023-04-08 07:11

from django.db import migrations
import django_migration_linter as linter


class Migration(migrations.Migration):

    dependencies = [
        ('twilioapp', '0002_auto_20220604_1008'),
    ]

    state_operations = [
        migrations.DeleteModel('PhoneCall'),
        migrations.DeleteModel('SMSMessage')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations
        )
    ]
