# Generated by Django 3.2.20 on 2023-08-02 17:56

from django.db import migrations


def remove_unused_dynamic_settings(apps, schema_editor):
    """
    These are deprecated dynamic settings that no longer have references and should be dropped
    """
    DynamicSetting = apps.get_model("base", "DynamicSetting")

    DynamicSetting.objects.filter(
        name__in=[
            "enabled_web_schedules_orgs",
            "enabled_mobile_test_push",
            "enabled_webhooks_2_orgs",
            "org_id_to_enable_insight_logs",
            "messaging_backends_enabled_orgs",
            "mobile_app_settings",
            "is_grafana_integration_enabled",
            "skip_web_cache_for_alert_group",
            "postpone_distribute_alert",
            "async_alert_creation",
            "postpone_distribute_alert_task",
            "postpone_create_alert_task",
            "simulate_slack_downtime",
            "skip_invalidate_web_cache_for_alert_group",
            "enabled_final_schedule_export",
            "self_hosted_invitations",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0004_auto_20230616_1510"),
    ]

    operations = [
        migrations.RunPython(remove_unused_dynamic_settings, migrations.RunPython.noop),
    ]
