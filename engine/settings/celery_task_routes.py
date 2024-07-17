CELERY_TASK_ROUTES = {
    # DEFAULT
    "apps.alerts.tasks.sync_grafana_alerting_contact_points.disconnect_integration_from_alerting_contact_points": {
        "queue": "default"
    },
    "apps.alerts.tasks.delete_alert_group.delete_alert_group": {"queue": "default"},
    "apps.alerts.tasks.delete_alert_group.send_alert_group_signal_for_delete": {"queue": "default"},
    "apps.alerts.tasks.delete_alert_group.finish_delete_alert_group": {"queue": "default"},
    "apps.alerts.tasks.invalidate_web_cache_for_alert_group.invalidate_web_cache_for_alert_group": {"queue": "default"},
    "apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal": {"queue": "default"},
    "apps.alerts.tasks.wipe.wipe": {"queue": "default"},
    "common.oncall_gateway.tasks.create_oncall_connector_async": {"queue": "default"},
    "common.oncall_gateway.tasks.delete_oncall_connector_async": {"queue": "default"},
    "common.oncall_gateway.tasks.create_slack_connector_async_v2": {"queue": "default"},
    "common.oncall_gateway.tasks.delete_slack_connector_async_v2": {"queue": "default"},
    "apps.heartbeat.tasks.integration_heartbeat_checkup": {"queue": "default"},
    "apps.heartbeat.tasks.process_heartbeat_task": {"queue": "default"},
    "apps.labels.tasks.update_labels_cache": {"queue": "default"},
    "apps.labels.tasks.update_instances_labels_cache": {"queue": "default"},
    "apps.labels.tasks.update_label_option_cache": {"queue": "default"},
    "apps.labels.tasks.update_label_pairs_cache": {"queue": "default"},
    "apps.metrics_exporter.tasks.start_calculate_and_cache_metrics": {"queue": "default"},
    "apps.metrics_exporter.tasks.update_metrics_for_alert_group": {"queue": "default"},
    "apps.metrics_exporter.tasks.update_metrics_for_user": {"queue": "default"},
    "apps.metrics_exporter.tasks.start_recalculation_for_new_metric": {"queue": "default"},
    "apps.metrics_exporter.tasks.save_organizations_ids_in_cache": {"queue": "default"},
    "apps.mobile_app.tasks.new_shift_swap_request.notify_shift_swap_requests": {"queue": "default"},
    "apps.mobile_app.tasks.new_shift_swap_request.notify_shift_swap_request": {"queue": "default"},
    "apps.mobile_app.tasks.new_shift_swap_request.notify_user_about_shift_swap_request": {"queue": "default"},
    "apps.mobile_app.tasks.new_shift_swap_request.notify_beneficiary_about_taken_shift_swap_request": {
        "queue": "default"
    },
    "apps.schedules.tasks.refresh_ical_files.refresh_ical_file": {"queue": "default"},
    "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_files": {"queue": "default"},
    "apps.schedules.tasks.refresh_ical_files.refresh_ical_final_schedule": {"queue": "default"},
    "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_final_schedules": {"queue": "default"},
    "apps.schedules.tasks.check_gaps_and_empty_shifts.check_gaps_and_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_notify_about_gaps_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.check_gaps_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.notify_about_gaps_in_schedule_task": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.schedule_notify_about_gaps_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_check_gaps_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_gaps_in_schedule.start_notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.check_empty_shifts_in_schedule": {"queue": "default"},
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.notify_about_empty_shifts_in_schedule_task": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_check_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.schedule_notify_about_empty_shifts_in_schedule": {
        "queue": "default"
    },
    "apps.schedules.tasks.shift_swaps.slack_messages.create_shift_swap_request_message": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.slack_messages.update_shift_swap_request_message": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.notify_when_taken.notify_beneficiary_about_taken_shift_swap_request": {
        "queue": "default"
    },
    "apps.schedules.tasks.shift_swaps.slack_followups.send_shift_swap_request_slack_followups": {"queue": "default"},
    "apps.schedules.tasks.shift_swaps.slack_followups.send_shift_swap_request_slack_followup": {"queue": "default"},
    "apps.migration_tool.tasks.start_migration_from_old_amixr": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_schedules": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_integrations": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_routes": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_escalation_policies": {"queue": "default"},
    "apps.migration_tool.tasks.start_migration_alert_groups": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_alert_group": {"queue": "default"},
    "apps.migration_tool.tasks.start_migration_alerts": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_alert": {"queue": "default"},
    "apps.migration_tool.tasks.start_migration_logs": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_log": {"queue": "default"},
    "apps.migration_tool.tasks.start_migration_user_data": {"queue": "default"},
    "apps.migration_tool.tasks.migrate_user_data": {"queue": "default"},
    "celery.backend_cleanup": {"queue": "default"},
    "apps.heartbeat.tasks.check_heartbeats": {"queue": "default"},
    "apps.oss_installation.tasks.send_cloud_heartbeat_task": {"queue": "default"},
    "apps.oss_installation.tasks.send_usage_stats_report": {"queue": "default"},
    "apps.oss_installation.tasks.sync_users_with_cloud": {"queue": "default"},
    "common.oncall_gateway.tasks.link_slack_team_async": {"queue": "default"},
    "common.oncall_gateway.tasks.unlink_slack_team_async": {"queue": "default"},
    "common.oncall_gateway.tasks.register_oncall_tenant_async": {"queue": "default"},
    "common.oncall_gateway.tasks.unregister_oncall_tenant_async": {"queue": "default"},
    "apps.chatops_proxy.tasks.link_slack_team_async": {"queue": "default"},
    "apps.chatops_proxy.tasks.unlink_slack_team_async": {"queue": "default"},
    "apps.chatops_proxy.tasks.register_oncall_tenant_async": {"queue": "default"},
    "apps.chatops_proxy.tasks.unregister_oncall_tenant_async": {"queue": "default"},
    # CRITICAL
    "apps.alerts.tasks.acknowledge_reminder.acknowledge_reminder_task": {"queue": "critical"},
    "apps.alerts.tasks.acknowledge_reminder.unacknowledge_timeout_task": {"queue": "critical"},
    "apps.alerts.tasks.distribute_alert.send_alert_create_signal": {"queue": "critical"},
    "apps.alerts.tasks.escalate_alert_group.escalate_alert_group": {"queue": "critical"},
    "apps.alerts.tasks.invite_user_to_join_incident.invite_user_to_join_incident": {"queue": "critical"},
    "apps.alerts.tasks.maintenance.check_maintenance_finished": {"queue": "critical"},
    "apps.alerts.tasks.maintenance.disable_maintenance": {"queue": "critical"},
    "apps.alerts.tasks.notify_all.notify_all_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_group.notify_group_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_team_members.notify_team_members_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_ical_schedule_shift.notify_ical_schedule_shift": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.notify_user_task": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.perform_notification": {"queue": "critical"},
    "apps.alerts.tasks.notify_user.send_bundled_notification": {"queue": "critical"},
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
    "apps.google.tasks.sync_out_of_office_calendar_events_for_all_users": {"queue": "critical"},
    "apps.google.tasks.sync_out_of_office_calendar_events_for_user": {"queue": "critical"},
    "apps.integrations.tasks.create_alert": {"queue": "critical"},
    "apps.integrations.tasks.create_alertmanager_alerts": {"queue": "critical"},
    "apps.integrations.tasks.start_notify_about_integration_ratelimit": {"queue": "critical"},
    "apps.mobile_app.tasks.new_alert_group.notify_user_about_new_alert_group": {"queue": "critical"},
    "apps.mobile_app.tasks.going_oncall_notification.conditionally_send_going_oncall_push_notifications_for_schedule": {
        "queue": "critical"
    },
    "apps.mobile_app.tasks.going_oncall_notification.conditionally_send_going_oncall_push_notifications_for_all_schedules": {
        "queue": "critical"
    },
    "apps.mobile_app.fcm_relay.fcm_relay_async": {"queue": "critical"},
    "apps.phone_notifications.phone_backend.notify_by_sms_bundle_async_task": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_for_custom_events_for_organization": {"queue": "critical"},
    "apps.schedules.tasks.drop_cached_ical.drop_cached_ical_task": {"queue": "critical"},
    # GRAFANA
    "apps.grafana_plugin.tasks.sync.plugin_sync_organization_async": {"queue": "grafana"},
    # LONG
    "apps.alerts.tasks.alert_group_web_title_cache.update_web_title_cache_for_alert_receive_channel": {"queue": "long"},
    "apps.alerts.tasks.alert_group_web_title_cache.update_web_title_cache": {"queue": "long"},
    "apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task": {"queue": "long"},
    "apps.alerts.tasks.check_escalation_finished.check_alert_group_personal_notifications_task": {"queue": "long"},
    "apps.alerts.tasks.check_escalation_finished.check_personal_notifications_task": {"queue": "long"},
    "apps.chatops_proxy.tasks.start_sync_org_with_chatops_proxy": {"queue": "long"},
    "apps.chatops_proxy.tasks.sync_org_with_chatops_proxy": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.cleanup_organization_async": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.cleanup_empty_deleted_integrations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_cleanup_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_integrations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_sync_organizations": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.sync_organization_async": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.sync_team_members_for_organization_async": {"queue": "long"},
    "apps.grafana_plugin.tasks.sync.start_sync_regions": {"queue": "long"},
    "apps.metrics_exporter.tasks.calculate_and_cache_metrics": {"queue": "long"},
    "apps.metrics_exporter.tasks.calculate_and_cache_user_was_notified_metric": {"queue": "long"},
    # SLACK
    "apps.integrations.tasks.notify_about_integration_ratelimit_in_slack": {"queue": "slack"},
    "apps.slack.helpers.alert_group_representative.on_alert_group_action_triggered_async": {"queue": "slack"},
    "apps.slack.helpers.alert_group_representative.on_create_alert_slack_representative_async": {"queue": "slack"},
    "apps.slack.tasks.clean_slack_channel_leftovers": {"queue": "slack"},
    "apps.slack.tasks.check_slack_message_exists_before_post_message_to_thread": {"queue": "slack"},
    "apps.slack.tasks.clean_slack_integration_leftovers": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_channels": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_channels_for_team": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_user_identities": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_usergroups": {"queue": "slack"},
    "apps.slack.tasks.populate_slack_usergroups_for_team": {"queue": "slack"},
    "apps.slack.tasks.post_slack_rate_limit_message": {"queue": "slack"},
    "apps.slack.tasks.send_message_to_thread_if_bot_not_in_channel": {"queue": "slack"},
    "apps.slack.tasks.start_update_slack_user_group_for_schedules": {"queue": "slack"},
    "apps.slack.tasks.unpopulate_slack_user_identities": {"queue": "slack"},
    "apps.slack.tasks.update_incident_slack_message": {"queue": "slack"},
    "apps.slack.tasks.update_slack_user_group_for_schedules": {"queue": "slack"},
    "apps.slack.representatives.alert_group_representative.on_create_alert_slack_representative_async": {
        "queue": "slack"
    },
    "apps.slack.representatives.alert_group_representative.on_alert_group_action_triggered_async": {"queue": "slack"},
    # TELEGRAM
    "apps.telegram.tasks.edit_message": {"queue": "telegram"},
    "apps.telegram.tasks.on_create_alert_telegram_representative_async": {"queue": "telegram"},
    "apps.telegram.tasks.register_telegram_webhook": {"queue": "telegram"},
    "apps.telegram.tasks.send_link_to_channel_message_or_fallback_to_full_alert_group": {"queue": "telegram"},
    "apps.telegram.tasks.send_log_and_actions_message": {"queue": "telegram"},
    "apps.telegram.tasks.on_alert_group_action_triggered_async": {"queue": "telegram"},
    # WEBHOOK
    "apps.alerts.tasks.custom_webhook_result.custom_webhook_result": {"queue": "webhook"},
    "apps.webhooks.tasks.trigger_webhook.execute_webhook": {"queue": "webhook"},
    "apps.webhooks.tasks.trigger_webhook.send_webhook_event": {"queue": "webhook"},
    "apps.webhooks.tasks.alert_group_status.alert_group_created": {"queue": "webhook"},
    "apps.webhooks.tasks.alert_group_status.alert_group_status_change": {"queue": "webhook"},
}
