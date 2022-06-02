export enum UserAction {
  UpdateIncidents = 'update_incidents',
  UpdateAlertReceiveChannels = 'update_alert_receive_channels',
  UpdateEscalationPolicies = 'update_escalation_policies',
  UpdateNotificationPolicies = 'update_notification_policies',
  UpdateGeneralLogChannelId = 'update_general_log_channel_id',
  UpdateGlobalSettings = 'update_global_settings',
  UpdateOwnSettings = 'update_own_settings',
  UpdateOtherUsersSettings = 'update_other_users_settings',
  ViewOtherUsers = 'view_other_users',
  UpdateIntegrations = 'update_integrations',
  UpdateSchedules = 'update_schedules',
  UpdateCustomActions = 'update_custom_actions',
  UpdateApiTokens = 'update_api_tokens',
  UpdateMaintenances = 'update_maintenances',
  CreateTeam = 'create_team',
  UpdateTeams = 'update_teams',
  SendDemoAlert = 'send_demo_alert',
  UpdateCurler = 'update_curler',

  // for testing purposes
  Impossible = 'impossible',
}
