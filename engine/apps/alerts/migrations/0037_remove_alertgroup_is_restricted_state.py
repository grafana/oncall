# Generated by Django 4.2.6 on 2023-11-03 23:02

import common.migrations.remove_field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0036_alertgroup_grafana_incident_id'),
    ]

    operations = [
        common.migrations.remove_field.RemoveFieldState(
            model_name='AlertGroup',
            name='is_restricted',
        ),
    ]
