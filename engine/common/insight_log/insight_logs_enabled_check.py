from django.apps import apps


def is_insight_logs_enabled(organization):
    """
    is_insight_logs_enabled checks if inside logs enabled for given organization.
    """
    DynamicSetting = apps.get_model("base", "DynamicSetting")
    org_id_to_enable_insight_logs, _ = DynamicSetting.objects.get_or_create(
        name="org_id_to_enable_insight_logs",
        defaults={"json_value": []},
    )
    log_all = "all" in org_id_to_enable_insight_logs.json_value
    insight_logs_enabled = organization.id in org_id_to_enable_insight_logs.json_value
    return log_all or insight_logs_enabled
