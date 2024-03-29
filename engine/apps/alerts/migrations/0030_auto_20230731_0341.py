# Generated by Django 3.2.19 on 2023-07-31 03:41

from django.db import migrations


integration_alertmanager = "alertmanager"
integration_grafana_alerting = "grafana_alerting"

legacy_alertmanager = "legacy_alertmanager"
legacy_grafana_alerting = "legacy_grafana_alerting"


def make_integrations_legacy(apps, schema_editor):
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")


    AlertReceiveChannel.objects.filter(integration=integration_alertmanager).update(integration=legacy_alertmanager)
    AlertReceiveChannel.objects.filter(integration=integration_grafana_alerting).update(integration=legacy_grafana_alerting)


def revert_make_integrations_legacy(apps, schema_editor):
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")


    AlertReceiveChannel.objects.filter(integration=legacy_alertmanager).update(integration=integration_alertmanager)
    AlertReceiveChannel.objects.filter(integration=legacy_grafana_alerting).update(integration=integration_grafana_alerting)


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0029_auto_20230728_0802'),
    ]

    operations = [
        migrations.RunPython(make_integrations_legacy, revert_make_integrations_legacy),
    ]
