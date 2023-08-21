import os

from .base import *  # noqa: F401, F403

try:
    import uwsgi
    from prometheus_client import multiprocess

    def on_uwsgi_worker_exit():
        multiprocess.mark_process_dead(os.getpid())

        uwsgi.atexit = on_uwsgi_worker_exit

except ModuleNotFoundError:
    # Only works under uwsgi web server environment
    pass


SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_SIGNING_SECRET_LIVE = os.environ.get("SLACK_SIGNING_SECRET_LIVE", "")


STATICFILES_DIRS = [
    "/etc/app/static",
]
STATIC_ROOT = "./collected_static/"

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [
    "^health/",
    "^health",
    "^ready/",
    "^ready",
    "^startupprobe/",
    "^startupprobe",
    "^ready_health_check/",
    "^ready_health_check",
    "^live_health_check/",
    "^live_health_check",
    "^django-prometheus/metrics",
    "^django-prometheus/metrics/",
]
SECURE_HSTS_SECONDS = 360000

CELERY_TASK_ROUTES = {
    # DEFAULT
    "apps.alerts.tasks.create_contact_points_for_datasource.create_contact_points_for_datasource": {"queue": "default"},
    "apps.alerts.tasks.sync_grafana_alerting_contact_points.sync_grafana_alerting_contact_points": {"queue": "default"},
    "apps.alerts.tasks.sync_grafana_alerting_contact_points.disconnect_integration_from_alerting_contact_points": {
        "queue": "default"
    },
    "apps.alerts.tasks.delete_alert_group.delete_alert_group": {"queue": "default"},
    "apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal": {"queue": "default"},
    "apps.alerts.tasks.wipe.wipe": {"queue": "default"},
    "apps.heartbeat.tasks.integration_heartbeat_checkup": {"queue": "default"},
    "apps.heartbeat.tasks.process_heartbeat_task": {"queue": "default"},
    "apps.metrics_exporter.tasks.start_calculate_and_cache_metrics": {"queue": "default"},
    "apps.metrics_exporter.tasks.start_recalculation_for_new_metric": {"queue": "default"},
    "apps.metrics_exporter.tasks.save_organizations_ids_in_cache": {"queue": "default"},
    "apps.mobile_app.tasks.notify_shift_swap_requests": {"queue": "default"},
    "apps.mobile_app.tasks.notify_shift_swap_request": {"queue": "default"},
    "apps.mobile_app.tasks.notify_user_about_shift_swap_request": {"queue": "default"},
    "apps.schedules.tasks.refresh_ical_files.refresh_ical_file": {"queue": "default"},
    "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_files": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.notify_about_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_check_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.shift_swaps.slack_messages.create_shift_swap_request_message": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.slack_messages.update_shift_swap_request_message": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.slack_followups.send_shift_swap_request_slack_followups": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.slack_followups.send_shift_swap_request_slack_followup": {"queue": "default"},
    # CRITICAL
    "apps.alerts.tasks.acknowledge_reminder.acknowledge_reminder_task": {"queue": "critical"},
    "apps.alerts.tasks.acknowledge_reminder.unacknowledge_timeout_task": {"queue": "critical"},
    "apps.alerts.tasks.distribute_alert.distribute_alert": {"queue": "critical"},
    "apps.alerts.tasks.distribute_alert.send_alert_create_signal": {"queue": "critical"},
    "apps.alerts.tasks.escalate_alert_group.escalate_alert_group": {"queue": "critical"},
    "apps.alerts.tasks.invite_user_to_join_incident.invite_user_to_join_incident": {"queue": "critical"},
    "apps.alerts.tasks.maintenance.check_maintenance_finished": {"queue": "critical"},
    "apps.alerts.tasks.maintenance.disable_maintenance": {"queue": "critical"},
    "apps.alerts.tasks.notify_all.notify_all_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_group.notify_group_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_ical_schedule_shift.notify_ical_schedule_shift": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.notify_user_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.perform_notification": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.send_user_notification_signal": {"queue": "critical"},
    "apps.alerts.tasks.resolve_alert_group_by_source_if_needed.resolve_alert_group_by_source_if_needed": {
        "queue": "critical"
    },
    "apps.alerts.tasks.resolve_by_last_step.resolve_by_last_step_task": {"queue": "critical"},
    "apps.alerts.tasks.send_update_log_report_signal.send_update_log_report_signal": {"queue": "critical"},
    "apps.alerts.tasks.send_update_resolution_note_signal.send_update_resolution_note_signal": {"queue": "critical"},
    "apps.alerts.tasks.unsilence.unsilence_task": {"queue": "critical"},
    "apps.base.tasks.process_failed_to_invoke_celery_tasks": {"queue": "critical"},
    "apps.base.tasks.process_failed_to_invoke_celery_tasks_batch": {"queue": "critical"},
    "apps.email.tasks.notify_user_async": {"queue": "critical"},
    "apps.integrations.tasks.create_alert": {"queue": "critical"},
    "apps.integrations.tasks.create_alertmanager_alerts": {"queue": "critical"},
    "apps.integrations.tasks.start_notify_about_integration_ratelimit": {"queue": "critical"},
    "apps.mobile_app.tasks.notify_user_async": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_for_custom_events_for_organization": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_task": {"queue": "critical"},
    # LONG
    "apps.alerts.tasks.alert_group_web_title_cache.update_web_title_cache_for_alert_receive_channel": {"queue": "long"},
    "apps.alerts.tasks.alert_group_web_title_cache.update_web_title_cache": {"queue": "long"},
    "apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.cleanup_organization_async": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_sync_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.sync_organization_async": {"queue": "long"},
    "apps.metrics_exporter.tasks.calculate_and_cache_metrics": {"queue": "long"},
    "apps.metrics_exporter.tasks.calculate_and_cache_user_was_notified_metric": {"queue": "long"},
    # SLACK
    "apps.integrations.tasks.notify_about_integration_ratelimit_in_slack": {"queue": "slack"},
    "apps.slack.helpers.alert_group_representative.on_alert_group_action_triggered_async": {"queue": "slack"},
    "apps.slack.helpers.alert_group_representative.on_alert_group_update_log_report_async": {"queue": "slack"},
    "apps.slack.helpers.alert_group_representative.on_create_alert_slack_representative_async": {"queue": "slack"},
    "apps.slack.tasks.check_slack_message_exists_before_post_message_to_thread": {"queue": "slack"},
    "apps.slack.tasks.clean_slack_integration_leftovers": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_channels": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_channels_for_team": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_user_identities": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_usergroups": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_usergroups_for_team": {"queue": "slack"},
    "apps.slack.tasks.post_or_update_log_report_message_task": {"queue": "slack"},
    "apps.slack.tasks.post_slack_rate_limit_message": {"queue": "slack"},
    "apps.slack.tasks.send_message_to_thread_if_bot_not_in_channel": {"queue": "slack"},
    "apps.slack.tasks.start_update_slack_user_group_for_schedules": {"queue": "slack"},
    "apps.slack.tasks.unpopulate_slack_user_identities": {"queue": "slack"},
    "apps.slack.tasks.update_incident_slack_message": {"queue": "slack"},
    "apps.slack.tasks.update_slack_user_group_for_schedules": {"queue": "slack"},
    # TELEGRAM
    "apps.telegram.tasks.edit_message": {"queue": "telegram"},
    "apps.telegram.tasks.on_create_alert_telegram_representative_async": {"queue": "telegram"},
    "apps.telegram.tasks.register_telegram_webhook": {"queue": "telegram"},
    "apps.telegram.tasks.send_link_to_channel_message_or_fallback_to_full_alert_group": {"queue": "telegram"},
    "apps.telegram.tasks.send_log_and_actions_message": {"queue": "telegram"},
    # WEBHOOK
    "apps.alerts.tasks.custom_button_result.custom_button_result": {"queue": "webhook"},
    "apps.mobile_app.fcm_relay.fcm_relay_async": {"queue": "webhook"},
}

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
