# This is temporary solution to not to hardcode permissions on frontend
# Is should be removed with one which will collect permission from action_permission views' attribute
ALL_PERMISSIONS = [
    "update_incidents",
    "update_alert_receive_channels",
    "update_escalation_policies",
    "update_notification_policies",
    "update_general_log_channel_id",
    "update_own_settings",
    "update_other_users_settings",
    "update_integrations",
    "update_schedules",
    "update_custom_actions",
    "update_api_tokens",
    "update_teams",
    "update_maintenances",
    "update_global_settings",
    "send_demo_alert",
    "view_other_users",
]
ADMIN_PERMISSIONS = ALL_PERMISSIONS
EDITOR_PERMISSIONS = ["update_incidents", "update_own_settings", "view_other_users"]
ALL_ROLES_PERMISSIONS = []
