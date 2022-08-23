import os

try:
    import uwsgi
    from prometheus_client import multiprocess

    def on_uwsgi_worker_exit():
        multiprocess.mark_process_dead(os.getpid())

        uwsgi.atexit = on_uwsgi_worker_exit

except ModuleNotFoundError:
    # Only works under uwsgi web server environment
    pass

from .base import *  # noqa

# It's required for collectstatic to avoid connecting it to MySQL

# Primary database must have the name "default"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),  # noqa
    }
}

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": [
            os.environ.get("REDIS_URI"),
        ],
        "OPTIONS": {
            "DB": 1,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    },
}

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_SIGNING_SECRET_LIVE = os.environ.get("SLACK_SIGNING_SECRET_LIVE", "")


STATICFILES_DIRS = [
    "/etc/app/static",
]
STATIC_ROOT = "./collected_static/"

DEBUG = False

CELERY_BROKER_URL = os.environ["RABBIT_URI"]

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
    "apps.alerts.tasks.call_ack_url.call_ack_url": {"queue": "default"},
    "apps.alerts.tasks.cache_alert_group_for_web.cache_alert_group_for_web": {"queue": "default"},
    "apps.alerts.tasks.cache_alert_group_for_web.schedule_cache_for_alert_group": {"queue": "default"},
    "apps.alerts.tasks.create_contact_points_for_datasource.create_contact_points_for_datasource": {"queue": "default"},
    "apps.alerts.tasks.sync_grafana_alerting_contact_points.sync_grafana_alerting_contact_points": {"queue": "default"},
    "apps.alerts.tasks.delete_alert_group.delete_alert_group": {"queue": "default"},
    "apps.alerts.tasks.invalidate_web_cache_for_alert_group.invalidate_web_cache_for_alert_group": {
        "queue": "default"
    },  # todo: remove
    "apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal": {"queue": "default"},
    "apps.alerts.tasks.wipe.wipe": {"queue": "default"},
    "apps.heartbeat.tasks.heartbeat_checkup": {"queue": "default"},
    "apps.heartbeat.tasks.integration_heartbeat_checkup": {"queue": "default"},
    "apps.heartbeat.tasks.process_heartbeat_task": {"queue": "default"},
    "apps.heartbeat.tasks.restore_heartbeat_tasks": {"queue": "default"},
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
    "engine.views.health_check_task": {"queue": "default"},
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
    "apps.alerts.tasks.send_update_postmortem_signal.send_update_postmortem_signal": {"queue": "critical"},
    "apps.alerts.tasks.send_update_resolution_note_signal.send_update_resolution_note_signal": {"queue": "critical"},
    "apps.alerts.tasks.unsilence.unsilence_task": {"queue": "critical"},
    "apps.base.tasks.process_failed_to_invoke_celery_tasks": {"queue": "critical"},
    "apps.base.tasks.process_failed_to_invoke_celery_tasks_batch": {"queue": "critical"},
    "apps.integrations.tasks.create_alert": {"queue": "critical"},
    "apps.integrations.tasks.create_alertmanager_alerts": {"queue": "critical"},
    "apps.integrations.tasks.start_notify_about_integration_ratelimit": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_for_custom_events_for_organization": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_task": {"queue": "critical"},
    # LONG
    "apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_sync_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.sync_organization_async": {"queue": "long"},
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
    "apps.slack.tasks.refresh_slack_user_identity_emails": {"queue": "slack"},
    "apps.slack.tasks.resolve_archived_incidents_for_organization": {"queue": "slack"},
    "apps.slack.tasks.send_debug_message_to_thread": {"queue": "slack"},
    "apps.slack.tasks.send_message_to_thread_if_bot_not_in_channel": {"queue": "slack"},
    "apps.slack.tasks.start_update_slack_user_group_for_schedules": {"queue": "slack"},
    "apps.slack.tasks.unarchive_incidents_for_organization": {"queue": "slack"},
    "apps.slack.tasks.unpopulate_slack_user_identities": {"queue": "slack"},
    "apps.slack.tasks.update_incident_slack_message": {"queue": "slack"},
    "apps.slack.tasks.update_slack_user_group_for_schedules": {"queue": "slack"},
    # TELEGRAM
    "apps.telegram.tasks.edit_message": {"queue": "telegram"},
    "apps.telegram.tasks.on_create_alert_telegram_representative_async": {"queue": "telegram"},
    "apps.telegram.tasks.register_telegram_webhook": {"queue": "telegram"},
    "apps.telegram.tasks.send_link_to_channel_message_or_fallback_to_full_incident": {"queue": "telegram"},
    "apps.telegram.tasks.send_log_and_actions_message": {"queue": "telegram"},
    # WEBHOOK
    "apps.alerts.tasks.custom_button_result.custom_button_result": {"queue": "webhook"},
}

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}
