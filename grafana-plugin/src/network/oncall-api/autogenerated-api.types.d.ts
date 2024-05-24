import type { CustomApiSchemas } from './types-generator/custom-schemas';

export interface paths {
  '/alert_receive_channels/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_list'];
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_retrieve'];
    /** @description Internal API endpoints for alert receive channels (integrations). */
    put: operations['alert_receive_channels_update'];
    post?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    delete: operations['alert_receive_channels_destroy'];
    options?: never;
    head?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    patch: operations['alert_receive_channels_partial_update'];
    trace?: never;
  };
  '/alert_receive_channels/{id}/api_token/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_api_token_retrieve'];
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_api_token_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/change_team/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    put: operations['alert_receive_channels_change_team_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/connect_contact_point/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_connect_contact_point_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/connected_alert_receive_channels/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_connected_alert_receive_channels_retrieve'];
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_connected_alert_receive_channels_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/connected_alert_receive_channels/{connected_alert_receive_channel_id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    put: operations['alert_receive_channels_connected_alert_receive_channels_update'];
    post?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    delete: operations['alert_receive_channels_connected_alert_receive_channels_destroy'];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/connected_contact_points/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_connected_contact_points_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/counters/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_counters_per_integration_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/create_contact_point/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_create_contact_point_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/disconnect_contact_point/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_disconnect_contact_point_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/migrate/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_migrate_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/preview_template/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Preview template */
    post: operations['alert_receive_channels_preview_template_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/send_demo_alert/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_send_demo_alert_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/start_maintenance/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_start_maintenance_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/status_options/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_status_options_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/stop_maintenance/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_stop_maintenance_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/test_connection/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_test_connection_create_2'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/webhooks/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_webhooks_list'];
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_webhooks_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/{id}/webhooks/{webhook_id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    put: operations['alert_receive_channels_webhooks_update'];
    post?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    delete: operations['alert_receive_channels_webhooks_destroy'];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/contact_points/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_contact_points_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/counters/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_counters_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/filters/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_filters_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/integration_options/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert receive channels (integrations). */
    get: operations['alert_receive_channels_integration_options_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/test_connection/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for alert receive channels (integrations). */
    post: operations['alert_receive_channels_test_connection_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alert_receive_channels/validate_name/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Checks if verbal_name is available.
     *     It is needed for OnCall <-> Alerting integration. */
    get: operations['alert_receive_channels_validate_name_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert groups. */
    get: operations['alertgroups_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Return alert group details.
     *
     *     It is worth mentioning that `render_after_resolve_report_json` property will return a list
     *     of log entries including actions involving the alert group, notifications triggered for a user
     *     and resolution notes updates.
     *
     *     A few additional notes about the possible values for each key in the logs:
     *
     *     - `time`: humanized time delta respect to now when the action took place
     *     - `action`: human-readable description of the action
     *     - `realm`: resource involved in the action; one of three possible values:
     *     `alert_group`, `user_notification`, `resolution_note`
     *     - `type`: integer value indicating the type of action (see below)
     *     - `created_at`: timestamp corresponding to when the action happened
     *     - `author`: details about the user performing the action
     *
     *     Possible `type` values depending on the realm value:
     *
     *     For `alert_group`:
     *     - 0: Acknowledged
     *     - 1: Unacknowledged
     *     - 2: Invite
     *     - 3: Stop invitation
     *     - 4: Re-invite
     *     - 5: Escalation triggered
     *     - 6: Invitation triggered
     *     - 7: Silenced
     *     - 8: Attached
     *     - 9: Unattached
     *     - 10: Custom button triggered
     *     - 11: Unacknowledged by timeout
     *     - 12: Failed attachment
     *     - 13: Incident resolved
     *     - 14: Incident unresolved
     *     - 15: Unsilenced
     *     - 16: Escalation finished
     *     - 17: Escalation failed
     *     - 18: Acknowledge reminder triggered
     *     - 19: Wiped
     *     - 20: Deleted
     *     - 21: Incident registered
     *     - 22: A route is assigned to the incident
     *     - 23: Trigger direct paging escalation
     *     - 24: Unpage a user
     *     - 25: Restricted
     *
     *     For `user_notification`:
     *     - 0: Personal notification triggered
     *     - 1: Personal notification finished
     *     - 2: Personal notification success,
     *     - 3: Personal notification failed
     *
     *     For `resolution_note`:
     *     - 0: slack
     *     - 1: web */
    get: operations['alertgroups_retrieve'];
    put?: never;
    post?: never;
    /** @description Internal API endpoints for alert groups. */
    delete: operations['alertgroups_destroy'];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/acknowledge/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Acknowledge an alert group */
    post: operations['alertgroups_acknowledge_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/attach/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Attach alert group to another alert group */
    post: operations['alertgroups_attach_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/escalation_snapshot/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for alert groups. */
    get: operations['alertgroups_escalation_snapshot_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/preview_template/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Preview template */
    post: operations['alertgroups_preview_template_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/resolve/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Resolve an alert group */
    post: operations['alertgroups_resolve_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/silence/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Silence an alert group for a specified delay */
    post: operations['alertgroups_silence_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/unacknowledge/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Unacknowledge an alert group */
    post: operations['alertgroups_unacknowledge_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/unattach/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Unattach an alert group that is already attached to another alert group */
    post: operations['alertgroups_unattach_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/unpage_user/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Remove a user that was directly paged for the alert group */
    post: operations['alertgroups_unpage_user_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/unresolve/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Unresolve an alert group */
    post: operations['alertgroups_unresolve_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/{id}/unsilence/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Unsilence a silenced alert group */
    post: operations['alertgroups_unsilence_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/bulk_action/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Perform a bulk action on a list of alert groups */
    post: operations['alertgroups_bulk_action_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/bulk_action_options/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Retrieve a list of valid bulk action options */
    get: operations['alertgroups_bulk_action_options_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/filters/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Retrieve a list of valid filter options that can be used to filter alert groups */
    get: operations['alertgroups_filters_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/labels/id/{key_id}': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Key with the list of values. IDs and names are interchangeable (see get_keys() for more details). */
    get: operations['alertgroups_labels_id_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/labels/keys/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description List of alert group label keys.
     *     IDs are the same as names to keep the response format consistent with LabelsViewSet.get_keys(). */
    get: operations['alertgroups_labels_keys_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/silence_options/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Retrieve a list of valid silence options */
    get: operations['alertgroups_silence_options_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/alertgroups/stats/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Return number of alert groups capped at 100001 */
    get: operations['alertgroups_stats_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/complete/{backend}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Authentication complete view */
    get: operations['complete_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/disconnect/{backend}': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get: operations['disconnect_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/features/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Return whitelist of enabled features.
     *     It is needed to disable features for On-prem installations. */
    get: operations['features_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/labels/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Create a new label key with values(Optional) */
    post: operations['labels_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/labels/id/{key_id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description get_key returns LabelOption – key with the list of values */
    get: operations['labels_id_retrieve'];
    /** @description Rename the key */
    put: operations['labels_id_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/labels/id/{key_id}/values/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Add a new value to the key */
    post: operations['labels_id_values_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/labels/id/{key_id}/values/{value_id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description get_value returns a Value */
    get: operations['labels_id_values_retrieve'];
    /** @description Rename the value */
    put: operations['labels_id_values_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/labels/keys/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description List of labels keys */
    get: operations['labels_keys_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/login/{backend}': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get: operations['login_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/login/{backend}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get: operations['login_retrieve_2'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_list'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_retrieve'];
    /** @description Internal API endpoints for users. */
    put: operations['users_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** @description Internal API endpoints for users. */
    patch: operations['users_partial_update'];
    trace?: never;
  };
  '/users/{id}/export_token/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_export_token_retrieve'];
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_export_token_create'];
    /** @description Internal API endpoints for users. */
    delete: operations['users_export_token_destroy'];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/forget_number/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** @description Internal API endpoints for users. */
    put: operations['users_forget_number_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/get_backend_verification_code/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_get_backend_verification_code_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/get_telegram_verification_code/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_get_telegram_verification_code_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/get_verification_call/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_get_verification_call_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/get_verification_code/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_get_verification_code_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/make_test_call/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_make_test_call_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/send_test_push/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_send_test_push_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/send_test_sms/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_send_test_sms_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/unlink_backend/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_unlink_backend_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/unlink_slack/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_unlink_slack_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/unlink_telegram/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Internal API endpoints for users. */
    post: operations['users_unlink_telegram_create'];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/upcoming_shifts/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_upcoming_shifts_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/{id}/verify_number/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** @description Internal API endpoints for users. */
    put: operations['users_verify_number_update'];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  '/users/timezone_options/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Internal API endpoints for users. */
    get: operations['users_timezone_options_retrieve'];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /**
     * @description * `acknowledge` - acknowledge
     *     * `resolve` - resolve
     *     * `silence` - silence
     *     * `restart` - restart
     * @enum {string}
     */
    ActionEnum: 'acknowledge' | 'resolve' | 'silence' | 'restart';
    AdditionalSettingsField: components['schemas']['Settings'];
    Alert: {
      readonly id: string;
      /** Format: uri */
      link_to_upstream_details?: string | null;
      readonly render_for_web: {
        title: string;
        message: string;
        image_url: string | null;
        source_link: string | null;
      };
      /** Format: date-time */
      readonly created_at: string;
    };
    AlertGroup: CustomApiSchemas['AlertGroup'] & {
      readonly pk: string;
      readonly alerts_count: number;
      inside_organization_number?: number;
      alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      resolved?: boolean;
      resolved_by?: components['schemas']['ResolvedByEnum'];
      resolved_by_user?: components['schemas']['FastUser'];
      /** Format: date-time */
      resolved_at?: string | null;
      /** Format: date-time */
      acknowledged_at?: string | null;
      acknowledged?: boolean;
      acknowledged_on_source?: boolean;
      acknowledged_by_user?: components['schemas']['FastUser'];
      silenced?: boolean;
      silenced_by_user?: components['schemas']['FastUser'];
      /** Format: date-time */
      silenced_at?: string | null;
      /** Format: date-time */
      silenced_until?: string | null;
      /** Format: date-time */
      readonly started_at: string;
      readonly related_users: components['schemas']['UserShort'][];
      readonly render_for_web:
        | {
            title: string;
            message: string;
            image_url: string | null;
            source_link: string | null;
          }
        | Record<string, never>;
      dependent_alert_groups: components['schemas']['ShortAlertGroup'][];
      root_alert_group: components['schemas']['ShortAlertGroup'];
      readonly status: number;
      /** @description Generate a link for AlertGroup to declare Grafana Incident by click */
      readonly declare_incident_link: string;
      team: string | null;
      grafana_incident_id?: string | null;
      readonly labels: components['schemas']['AlertGroupLabel'][];
      readonly permalinks: {
        slack: string | null;
        slack_app: string | null;
        telegram: string | null;
        web: string;
      };
      readonly alerts: components['schemas']['Alert'][];
      readonly render_after_resolve_report_json: {
        time: string;
        action: string;
        /** @enum {string} */
        realm: 'user_notification' | 'alert_group' | 'resolution_note';
        type: number;
        created_at: string;
        author: {
          username: string;
          pk: string;
          avatar: string;
          avatar_full: string;
        };
      }[];
      readonly slack_permalink: string | null;
      /** Format: date-time */
      readonly last_alert_at: string;
      readonly paged_users: {
        id: number;
        username: string;
        name: string;
        pk: string;
        avatar: string;
        avatar_full: string;
        important: boolean;
      }[];
      readonly external_urls: {
        integration: string;
        integration_type: string;
        external_id: string;
        url: string;
      }[];
    };
    AlertGroupAttach: {
      root_alert_group_pk: string;
    };
    AlertGroupBulkActionOptions: {
      value: components['schemas']['ActionEnum'];
      display_name: components['schemas']['ActionEnum'];
    };
    AlertGroupBulkActionRequest: {
      alert_group_pks: string[];
      action: components['schemas']['ActionEnum'];
      /** @description only applicable for silence */
      delay?: number | null;
    };
    AlertGroupFilters: {
      name: string;
      type: string;
      href?: string;
      global?: boolean;
      default?: {
        [key: string]: unknown;
      };
      description?: string;
      options: components['schemas']['AlertGroupFiltersOptions'];
    };
    AlertGroupFiltersOptions: {
      value: string;
      display_name: number;
    };
    AlertGroupLabel: {
      key: components['schemas']['Key'];
      value: components['schemas']['Value'];
    };
    AlertGroupList: {
      readonly pk: string;
      readonly alerts_count: number;
      inside_organization_number?: number;
      alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      resolved?: boolean;
      resolved_by?: components['schemas']['ResolvedByEnum'];
      resolved_by_user?: components['schemas']['FastUser'];
      /** Format: date-time */
      resolved_at?: string | null;
      /** Format: date-time */
      acknowledged_at?: string | null;
      acknowledged?: boolean;
      acknowledged_on_source?: boolean;
      acknowledged_by_user?: components['schemas']['FastUser'];
      silenced?: boolean;
      silenced_by_user?: components['schemas']['FastUser'];
      /** Format: date-time */
      silenced_at?: string | null;
      /** Format: date-time */
      silenced_until?: string | null;
      /** Format: date-time */
      readonly started_at: string;
      readonly related_users: components['schemas']['UserShort'][];
      readonly render_for_web:
        | {
            title: string;
            message: string;
            image_url: string | null;
            source_link: string | null;
          }
        | Record<string, never>;
      dependent_alert_groups: components['schemas']['ShortAlertGroup'][];
      root_alert_group: components['schemas']['ShortAlertGroup'];
      readonly status: number;
      /** @description Generate a link for AlertGroup to declare Grafana Incident by click */
      readonly declare_incident_link: string;
      team: string | null;
      grafana_incident_id?: string | null;
      readonly labels: components['schemas']['AlertGroupLabel'][];
      readonly permalinks: {
        slack: string | null;
        slack_app: string | null;
        telegram: string | null;
        web: string;
      };
    };
    AlertGroupResolve: {
      resolution_note?: string | null;
    };
    AlertGroupSilence: {
      delay: number;
    };
    AlertGroupSilenceOptions: {
      value: components['schemas']['AlertGroupSilenceOptionsValueEnum'];
      display_name: components['schemas']['AlertGroupSilenceOptionsDisplayNameEnum'];
    };
    /**
     * @description * `30 minutes` - 30 minutes
     *     * `1 hour` - 1 hour
     *     * `2 hours` - 2 hours
     *     * `3 hours` - 3 hours
     *     * `4 hours` - 4 hours
     *     * `6 hours` - 6 hours
     *     * `12 hours` - 12 hours
     *     * `16 hours` - 16 hours
     *     * `20 hours` - 20 hours
     *     * `24 hours` - 24 hours
     *     * `Forever` - Forever
     * @enum {string}
     */
    AlertGroupSilenceOptionsDisplayNameEnum:
      | '30 minutes'
      | '1 hour'
      | '2 hours'
      | '3 hours'
      | '4 hours'
      | '6 hours'
      | '12 hours'
      | '16 hours'
      | '20 hours'
      | '24 hours'
      | 'Forever';
    /**
     * @description * `1800` - 1800
     *     * `3600` - 3600
     *     * `7200` - 7200
     *     * `10800` - 10800
     *     * `14400` - 14400
     *     * `21600` - 21600
     *     * `43200` - 43200
     *     * `57600` - 57600
     *     * `72000` - 72000
     *     * `86400` - 86400
     *     * `-1` - -1
     * @enum {integer}
     */
    AlertGroupSilenceOptionsValueEnum: 1800 | 3600 | 7200 | 10800 | 14400 | 21600 | 43200 | 57600 | 72000 | 86400 | -1;
    AlertGroupStats: {
      count: number;
    };
    AlertGroupUnpageUser: {
      user_id: string;
    };
    AlertReceiveChannel: {
      readonly id: string;
      readonly description: string | null;
      description_short?: string | null;
      integration: components['schemas']['IntegrationEnum'];
      readonly smile_code: string;
      verbal_name?: string | null;
      readonly author: string;
      readonly organization: string;
      team?: string | null;
      /** Format: date-time */
      readonly created_at: string;
      readonly integration_url: string | null;
      readonly alert_count: number;
      readonly alert_groups_count: number;
      allow_source_based_resolving?: boolean;
      readonly instructions: string;
      readonly is_able_to_autoresolve: boolean;
      readonly default_channel_filter: string | null;
      readonly demo_alert_enabled: boolean;
      readonly maintenance_mode:
        | (components['schemas']['MaintenanceModeEnum'] | components['schemas']['NullEnum'])
        | null;
      readonly maintenance_till: number | null;
      readonly heartbeat: components['schemas']['IntegrationHeartBeat'] | null;
      readonly is_available_for_integration_heartbeat: boolean;
      readonly allow_delete: boolean;
      readonly demo_alert_payload: {
        [key: string]: unknown;
      };
      readonly routes_count: number;
      readonly connected_escalations_chains_count: number;
      readonly is_based_on_alertmanager: boolean;
      readonly inbound_email: string;
      readonly is_legacy: boolean;
      labels?: components['schemas']['LabelPair'][];
      alert_group_labels?: components['schemas']['IntegrationAlertGroupLabels'];
      /** Format: date-time */
      readonly alertmanager_v2_migrated_at: string | null;
      additional_settings?: components['schemas']['AdditionalSettingsField'] | null;
    };
    AlertReceiveChannelConnectContactPoint: {
      datasource_uid: string;
      contact_point_name: string;
    };
    AlertReceiveChannelConnectedChannel: {
      readonly alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      backsync: boolean;
    };
    AlertReceiveChannelConnectedContactPoints: {
      uid: string;
      name: string;
      contact_points: components['schemas']['AlertReceiveChannelConnectedContactPointsInner'][];
    };
    AlertReceiveChannelConnectedContactPointsInner: {
      name: string;
      notification_connected: boolean;
    };
    AlertReceiveChannelConnection: {
      readonly source_alert_receive_channels: components['schemas']['AlertReceiveChannelSourceChannel'][];
      readonly connected_alert_receive_channels: components['schemas']['AlertReceiveChannelConnectedChannel'][];
    };
    AlertReceiveChannelContactPoints: {
      uid: string;
      name: string;
      contact_points: string[];
    };
    AlertReceiveChannelCreate: {
      readonly id: string;
      readonly description: string | null;
      description_short?: string | null;
      integration: components['schemas']['IntegrationEnum'];
      readonly smile_code: string;
      verbal_name?: string | null;
      readonly author: string;
      readonly organization: string;
      team?: string | null;
      /** Format: date-time */
      readonly created_at: string;
      readonly integration_url: string | null;
      readonly alert_count: number;
      readonly alert_groups_count: number;
      allow_source_based_resolving?: boolean;
      readonly instructions: string;
      readonly is_able_to_autoresolve: boolean;
      readonly default_channel_filter: string | null;
      readonly demo_alert_enabled: boolean;
      readonly maintenance_mode:
        | (components['schemas']['MaintenanceModeEnum'] | components['schemas']['NullEnum'])
        | null;
      readonly maintenance_till: number | null;
      readonly heartbeat: components['schemas']['IntegrationHeartBeat'] | null;
      readonly is_available_for_integration_heartbeat: boolean;
      readonly allow_delete: boolean;
      readonly demo_alert_payload: {
        [key: string]: unknown;
      };
      readonly routes_count: number;
      readonly connected_escalations_chains_count: number;
      readonly is_based_on_alertmanager: boolean;
      readonly inbound_email: string;
      readonly is_legacy: boolean;
      labels?: components['schemas']['LabelPair'][];
      alert_group_labels?: components['schemas']['IntegrationAlertGroupLabels'];
      /** Format: date-time */
      readonly alertmanager_v2_migrated_at: string | null;
      additional_settings?: components['schemas']['AdditionalSettingsField'] | null;
      /** @default true */
      create_default_webhooks: boolean;
    };
    AlertReceiveChannelCreateContactPoint: {
      datasource_uid: string;
      contact_point_name: string;
    };
    AlertReceiveChannelDisconnectContactPoint: {
      datasource_uid: string;
      contact_point_name: string;
    };
    AlertReceiveChannelFilters: {
      name: string;
      display_name?: string;
      type: string;
      href: string;
      global?: boolean;
    };
    AlertReceiveChannelIntegrationOptions: {
      value: string;
      display_name: string;
      short_description: string;
      featured: boolean;
      featured_tag_name: string | null;
    };
    AlertReceiveChannelNewConnection: {
      id: string;
      backsync: boolean;
    };
    AlertReceiveChannelPolymorphic:
      | components['schemas']['AlertReceiveChannel']
      | components['schemas']['FilterAlertReceiveChannel'];
    AlertReceiveChannelSendDemoAlert: {
      demo_alert_payload?: {
        [key: string]: unknown;
      } | null;
    };
    AlertReceiveChannelSourceChannel: {
      readonly alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      backsync: boolean;
    };
    AlertReceiveChannelStartMaintenance: {
      mode: components['schemas']['ModeEnum'];
      duration: components['schemas']['DurationEnum'];
    };
    AlertReceiveChannelUpdate: {
      readonly id: string;
      readonly description: string | null;
      description_short?: string | null;
      readonly integration: components['schemas']['IntegrationEnum'];
      readonly smile_code: string;
      verbal_name?: string | null;
      readonly author: string;
      readonly organization: string;
      team?: string | null;
      /** Format: date-time */
      readonly created_at: string;
      readonly integration_url: string | null;
      readonly alert_count: number;
      readonly alert_groups_count: number;
      allow_source_based_resolving?: boolean;
      readonly instructions: string;
      readonly is_able_to_autoresolve: boolean;
      readonly default_channel_filter: string | null;
      readonly demo_alert_enabled: boolean;
      readonly maintenance_mode:
        | (components['schemas']['MaintenanceModeEnum'] | components['schemas']['NullEnum'])
        | null;
      readonly maintenance_till: number | null;
      readonly heartbeat: components['schemas']['IntegrationHeartBeat'] | null;
      readonly is_available_for_integration_heartbeat: boolean;
      readonly allow_delete: boolean;
      readonly demo_alert_payload: {
        [key: string]: unknown;
      };
      readonly routes_count: number;
      readonly connected_escalations_chains_count: number;
      readonly is_based_on_alertmanager: boolean;
      readonly inbound_email: string;
      readonly is_legacy: boolean;
      labels?: components['schemas']['LabelPair'][];
      alert_group_labels?: components['schemas']['IntegrationAlertGroupLabels'];
      /** Format: date-time */
      readonly alertmanager_v2_migrated_at: string | null;
      additional_settings?: components['schemas']['AdditionalSettingsField'] | null;
    };
    /** @enum {integer} */
    CloudConnectionStatusEnum: 0 | 1 | 2 | 3;
    /** @description This serializer is consistent with apps.api.serializers.labels.LabelPairSerializer, but allows null for value ID. */
    CustomLabel: {
      key: components['schemas']['CustomLabelKey'];
      value: components['schemas']['CustomLabelValue'];
    };
    CustomLabelKey: {
      id: string;
      name: string;
      /** @default false */
      prescribed: boolean;
    };
    CustomLabelValue: {
      id: string | null;
      name: string;
      /** @default false */
      prescribed: boolean;
    };
    /**
     * @description * `3600` - 3600
     *     * `10800` - 10800
     *     * `21600` - 21600
     *     * `43200` - 43200
     *     * `86400` - 86400
     * @enum {integer}
     */
    DurationEnum: 3600 | 10800 | 21600 | 43200 | 86400;
    FastAlertReceiveChannel: {
      readonly id: string;
      readonly integration: string;
      verbal_name?: string | null;
      readonly deleted: boolean;
    };
    FastOrganization: {
      readonly pk: string;
      readonly name: string;
    };
    FastTeam: {
      readonly id: string;
      name: string;
      email?: string | null;
      /** Format: uri */
      avatar_url: string;
    };
    FastUser: {
      pk: string;
      readonly username: string;
    };
    FilterAlertReceiveChannel: {
      readonly value: string;
      readonly display_name: string;
      readonly integration_url: string | null;
    };
    FilterUser: {
      value: string;
      display_name: string;
    };
    GoogleCalendarSettings: {
      oncall_schedules_to_consider_for_shift_swaps?: string[] | null;
    };
    /** @description Alert group labels configuration for the integration. See AlertReceiveChannel.alert_group_labels for details. */
    IntegrationAlertGroupLabels: {
      inheritable: {
        [key: string]: boolean | undefined;
      };
      custom: components['schemas']['CustomLabel'][];
      template: string | null;
    };
    /**
     * @description * `alertmanager` - Alertmanager
     *     * `legacy_alertmanager` - (Legacy) AlertManager
     *     * `grafana` - Grafana
     *     * `grafana_alerting` - Grafana Alerting
     *     * `legacy_grafana_alerting` - (Legacy) Grafana Alerting
     *     * `formatted_webhook` - Formatted webhook
     *     * `webhook` - Webhook
     *     * `kapacitor` - Kapacitor
     *     * `elastalert` - Elastalert
     *     * `heartbeat` - Heartbeat
     *     * `inbound_email` - Inbound Email
     *     * `maintenance` - Maintenance
     *     * `manual` - Manual
     *     * `slack_channel` - Slack Channel
     *     * `zabbix` - Zabbix
     *     * `direct_paging` - Direct paging
     *     * `servicenow` - ServiceNow
     *     * `amazon_sns` - Amazon SNS
     *     * `stackdriver` - Stackdriver
     *     * `curler` - Curler
     *     * `datadog` - Datadog
     *     * `demo` - Demo
     *     * `fabric` - Fabric
     *     * `newrelic` - New Relic
     *     * `pagerduty` - Pagerduty
     *     * `pingdom` - Pingdom
     *     * `prtg` - PRTG
     *     * `sentry` - Sentry
     *     * `uptimerobot` - UptimeRobot
     *     * `jira` - Jira
     *     * `zendesk` - Zendesk
     *     * `appdynamics` - AppDynamics
     * @enum {string}
     */
    IntegrationEnum:
      | 'alertmanager'
      | 'legacy_alertmanager'
      | 'grafana'
      | 'grafana_alerting'
      | 'legacy_grafana_alerting'
      | 'formatted_webhook'
      | 'webhook'
      | 'kapacitor'
      | 'elastalert'
      | 'heartbeat'
      | 'inbound_email'
      | 'maintenance'
      | 'manual'
      | 'slack_channel'
      | 'zabbix'
      | 'direct_paging'
      | 'servicenow'
      | 'amazon_sns'
      | 'stackdriver'
      | 'curler'
      | 'datadog'
      | 'demo'
      | 'fabric'
      | 'newrelic'
      | 'pagerduty'
      | 'pingdom'
      | 'prtg'
      | 'sentry'
      | 'uptimerobot'
      | 'jira'
      | 'zendesk'
      | 'appdynamics';
    IntegrationHeartBeat: {
      readonly id: string;
      timeout_seconds: components['schemas']['TimeoutSecondsEnum'];
      alert_receive_channel: string;
      readonly link: string | null;
      readonly last_heartbeat_time_verbal: string | null;
      /** @description Return bool indicates heartbeat status.
       *     True if first heartbeat signal was sent and flow is ok else False.
       *     If first heartbeat signal was not send it means that configuration was not finished and status not ok. */
      readonly status: boolean;
      readonly instruction: string;
    };
    IntegrationTokenPostResponse: {
      token: string;
      usage: string;
    };
    Key: {
      id: string;
      name: string;
    };
    LabelCreate: {
      key: components['schemas']['LabelRepr'];
      values: components['schemas']['LabelRepr'][];
    };
    LabelKey: {
      id: string;
      name: string;
      /** @default false */
      prescribed: boolean;
    };
    LabelOption: {
      key: components['schemas']['LabelKey'];
      values: components['schemas']['LabelValue'][];
    };
    LabelPair: {
      key: components['schemas']['LabelKey'];
      value: components['schemas']['LabelValue'];
    };
    LabelRepr: {
      name: string;
    };
    LabelValue: {
      id: string;
      name: string;
      /** @default false */
      prescribed: boolean;
    };
    ListUser: {
      readonly pk: string;
      readonly organization: components['schemas']['FastOrganization'];
      current_team?: string | null;
      /** Format: email */
      readonly email: string;
      readonly username: string;
      readonly name: string;
      readonly role: components['schemas']['RoleEnum'];
      /** Format: uri */
      readonly avatar: string;
      /** Format: uri */
      readonly avatar_full: string;
      timezone?: string | null;
      working_hours?: components['schemas']['WorkingHours'];
      unverified_phone_number?: string | null;
      /** @description Use property to highlight that _verified_phone_number should not be modified directly */
      readonly verified_phone_number: string | null;
      readonly slack_user_identity: components['schemas']['SlackUserIdentity'];
      readonly telegram_configuration: components['schemas']['TelegramToUserConnector'];
      readonly messaging_backends: {
        [key: string]:
          | {
              [key: string]: unknown;
            }
          | undefined;
      };
      readonly notification_chain_verbal: {
        default: string;
        important: string;
      };
      readonly cloud_connection_status: components['schemas']['CloudConnectionStatusEnum'] | null;
      hide_phone_number?: boolean;
      readonly has_google_oauth2_connected: boolean;
    };
    /**
     * @description * `0` - Debug
     *     * `1` - Maintenance
     * @enum {integer}
     */
    MaintenanceModeEnum: 0 | 1;
    /**
     * @description * `0` - Debug
     *     * `1` - Maintenance
     * @enum {integer}
     */
    ModeEnum: 0 | 1;
    /** @enum {unknown} */
    NullEnum: null;
    PaginatedAlertGroupListList: {
      next?: string | null;
      previous?: string | null;
      results?: components['schemas']['AlertGroupList'][];
      page_size?: number;
    };
    PaginatedAlertReceiveChannelPolymorphicList: {
      /** @example 123 */
      count?: number;
      /**
       * Format: uri
       * @example http://api.example.org/accounts/?page=4
       */
      next?: string | null;
      /**
       * Format: uri
       * @example http://api.example.org/accounts/?page=2
       */
      previous?: string | null;
      results?: components['schemas']['AlertReceiveChannelPolymorphic'][];
      page_size?: number;
      current_page_number?: number;
      total_pages?: number;
    };
    PaginatedUserPolymorphicList: {
      /** @example 123 */
      count?: number;
      /**
       * Format: uri
       * @example http://api.example.org/accounts/?page=4
       */
      next?: string | null;
      /**
       * Format: uri
       * @example http://api.example.org/accounts/?page=2
       */
      previous?: string | null;
      results?: components['schemas']['UserPolymorphic'][];
      page_size?: number;
      current_page_number?: number;
      total_pages?: number;
    };
    PatchedAlertReceiveChannelUpdate: {
      readonly id?: string;
      readonly description?: string | null;
      description_short?: string | null;
      readonly integration?: components['schemas']['IntegrationEnum'];
      readonly smile_code?: string;
      verbal_name?: string | null;
      readonly author?: string;
      readonly organization?: string;
      team?: string | null;
      /** Format: date-time */
      readonly created_at?: string;
      readonly integration_url?: string | null;
      readonly alert_count?: number;
      readonly alert_groups_count?: number;
      allow_source_based_resolving?: boolean;
      readonly instructions?: string;
      readonly is_able_to_autoresolve?: boolean;
      readonly default_channel_filter?: string | null;
      readonly demo_alert_enabled?: boolean;
      readonly maintenance_mode?:
        | (components['schemas']['MaintenanceModeEnum'] | components['schemas']['NullEnum'])
        | null;
      readonly maintenance_till?: number | null;
      readonly heartbeat?: components['schemas']['IntegrationHeartBeat'] | null;
      readonly is_available_for_integration_heartbeat?: boolean;
      readonly allow_delete?: boolean;
      readonly demo_alert_payload?: {
        [key: string]: unknown;
      };
      readonly routes_count?: number;
      readonly connected_escalations_chains_count?: number;
      readonly is_based_on_alertmanager?: boolean;
      readonly inbound_email?: string;
      readonly is_legacy?: boolean;
      labels?: components['schemas']['LabelPair'][];
      alert_group_labels?: components['schemas']['IntegrationAlertGroupLabels'];
      /** Format: date-time */
      readonly alertmanager_v2_migrated_at?: string | null;
      additional_settings?: components['schemas']['AdditionalSettingsField'] | null;
    };
    PatchedUser: {
      readonly pk?: string;
      readonly organization?: components['schemas']['FastOrganization'];
      current_team?: string | null;
      /** Format: email */
      readonly email?: string;
      readonly username?: string;
      readonly name?: string;
      readonly role?: components['schemas']['RoleEnum'];
      /** Format: uri */
      readonly avatar?: string;
      /** Format: uri */
      readonly avatar_full?: string;
      timezone?: string | null;
      working_hours?: components['schemas']['WorkingHours'];
      unverified_phone_number?: string | null;
      /** @description Use property to highlight that _verified_phone_number should not be modified directly */
      readonly verified_phone_number?: string | null;
      readonly slack_user_identity?: components['schemas']['SlackUserIdentity'];
      readonly telegram_configuration?: components['schemas']['TelegramToUserConnector'];
      readonly messaging_backends?: {
        [key: string]:
          | {
              [key: string]: unknown;
            }
          | undefined;
      };
      readonly notification_chain_verbal?: {
        default: string;
        important: string;
      };
      readonly cloud_connection_status?: components['schemas']['CloudConnectionStatusEnum'] | null;
      hide_phone_number?: boolean;
      readonly has_google_oauth2_connected?: boolean;
      readonly is_currently_oncall?: boolean;
      google_calendar_settings?: components['schemas']['GoogleCalendarSettings'];
    };
    PreviewTemplateRequest: {
      template_body?: string | null;
      template_name?: string | null;
      payload?: {
        [key: string]: unknown;
      } | null;
    };
    PreviewTemplateResponse: {
      preview: string | null;
      is_valid_json_object: boolean;
    };
    /**
     * @description * `0` - source
     *     * `1` - user
     *     * `2` - not yet
     *     * `3` - last escalation step
     *     * `4` - archived
     *     * `5` - wiped
     *     * `6` - stop maintenance
     *     * `7` - not yet, autoresolve disabled
     * @enum {integer}
     */
    ResolvedByEnum: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
    /**
     * @description * `0` - ADMIN
     *     * `1` - EDITOR
     *     * `2` - VIEWER
     *     * `3` - NONE
     * @enum {integer}
     */
    RoleEnum: 0 | 1 | 2 | 3;
    Settings: {
      instance_url: string;
      username: string;
      password: string;
      /** @default {
       *       "firing": null,
       *       "acknowledged": null,
       *       "resolved": null,
       *       "silenced": null
       *     } */
      state_mapping: components['schemas']['StateMapping'];
      /** @default false */
      is_configured: boolean;
    };
    ShortAlertGroup: {
      readonly pk: string;
      readonly render_for_web:
        | {
            title: string;
            message: string;
            image_url: string | null;
            source_link: string | null;
          }
        | Record<string, never>;
      alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      readonly inside_organization_number: number;
    };
    SlackUserIdentity: {
      readonly slack_login: string;
      readonly slack_id: string;
      readonly avatar: string;
      readonly name: string;
      readonly display_name: string | null;
    };
    StateMapping: {
      firing: unknown[] | null;
      acknowledged: unknown[] | null;
      resolved: unknown[] | null;
      silenced: unknown[] | null;
    };
    TelegramToUserConnector: {
      telegram_nick_name?: string | null;
      /** Format: int64 */
      telegram_chat_id: number;
    };
    /**
     * @description * `60` - 1 minute
     *     * `120` - 2 minutes
     *     * `180` - 3 minutes
     *     * `300` - 5 minutes
     *     * `600` - 10 minutes
     *     * `900` - 15 minutes
     *     * `1800` - 30 minutes
     *     * `3600` - 1 hour
     *     * `43200` - 12 hours
     *     * `86400` - 1 day
     * @enum {integer}
     */
    TimeoutSecondsEnum: 60 | 120 | 180 | 300 | 600 | 900 | 1800 | 3600 | 43200 | 86400;
    User: CustomApiSchemas['User'] & {
      readonly pk: string;
      readonly organization: components['schemas']['FastOrganization'];
      current_team?: string | null;
      /** Format: email */
      readonly email: string;
      readonly username: string;
      readonly name: string;
      readonly role: components['schemas']['RoleEnum'];
      /** Format: uri */
      readonly avatar: string;
      /** Format: uri */
      readonly avatar_full: string;
      timezone?: string | null;
      working_hours?: components['schemas']['WorkingHours'];
      unverified_phone_number?: string | null;
      /** @description Use property to highlight that _verified_phone_number should not be modified directly */
      readonly verified_phone_number: string | null;
      readonly slack_user_identity: components['schemas']['SlackUserIdentity'];
      readonly telegram_configuration: components['schemas']['TelegramToUserConnector'];
      readonly messaging_backends: {
        [key: string]:
          | {
              [key: string]: unknown;
            }
          | undefined;
      };
      readonly notification_chain_verbal: {
        default: string;
        important: string;
      };
      readonly cloud_connection_status: components['schemas']['CloudConnectionStatusEnum'] | null;
      hide_phone_number?: boolean;
      readonly has_google_oauth2_connected: boolean;
      readonly is_currently_oncall: boolean;
      google_calendar_settings?: components['schemas']['GoogleCalendarSettings'];
    };
    UserExportTokenGetResponse: {
      /** Format: date-time */
      created_at: string;
      /** Format: date-time */
      revoked_at: string | null;
      active: boolean;
    };
    UserExportTokenPostResponse: {
      token: string;
      /** Format: date-time */
      created_at: string;
      export_url: string;
    };
    UserGetTelegramVerificationCode: {
      telegram_code: string;
      bot_link: string;
    };
    UserIsCurrentlyOnCall: {
      username: string;
      pk: string;
      avatar: string;
      avatar_full: string;
      name: string;
      readonly timezone: string | null;
      readonly teams: components['schemas']['FastTeam'][];
      readonly is_currently_oncall: boolean;
    };
    UserPolymorphic:
      | components['schemas']['FilterUser']
      | components['schemas']['UserIsCurrentlyOnCall']
      | components['schemas']['ListUser'];
    UserShort: {
      username: string;
      pk: string;
      avatar: string;
      avatar_full: string;
    };
    Value: {
      id: string;
      name: string;
    };
    Webhook: CustomApiSchemas['Webhook'] & {
      readonly id: string;
      name?: string | null;
      is_webhook_enabled?: boolean | null;
      is_legacy?: boolean | null;
      team?: string | null;
      username?: string | null;
      password?: string | null;
      authorization_header?: string | null;
      trigger_template?: string | null;
      headers?: string | null;
      url?: string | null;
      data?: string | null;
      forward_all?: boolean | null;
      http_method?: string | null;
      trigger_type: string | null;
      readonly trigger_type_name: string;
      readonly last_response_log: string;
      integration_filter?: string[];
      preset?: string | null;
      labels?: components['schemas']['LabelPair'][];
    };
    WorkingHours: {
      monday: components['schemas']['WorkingHoursPeriod'][];
      tuesday: components['schemas']['WorkingHoursPeriod'][];
      wednesday: components['schemas']['WorkingHoursPeriod'][];
      thursday: components['schemas']['WorkingHoursPeriod'][];
      friday: components['schemas']['WorkingHoursPeriod'][];
      saturday: components['schemas']['WorkingHoursPeriod'][];
      sunday: components['schemas']['WorkingHoursPeriod'][];
    };
    WorkingHoursPeriod: {
      start: string;
      end: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  alert_receive_channels_list: {
    parameters: {
      query?: {
        id_ne?: string[];
        /** @description * `alertmanager` - Alertmanager
         *     * `legacy_alertmanager` - (Legacy) AlertManager
         *     * `grafana` - Grafana
         *     * `grafana_alerting` - Grafana Alerting
         *     * `legacy_grafana_alerting` - (Legacy) Grafana Alerting
         *     * `formatted_webhook` - Formatted webhook
         *     * `webhook` - Webhook
         *     * `kapacitor` - Kapacitor
         *     * `elastalert` - Elastalert
         *     * `heartbeat` - Heartbeat
         *     * `inbound_email` - Inbound Email
         *     * `maintenance` - Maintenance
         *     * `manual` - Manual
         *     * `slack_channel` - Slack Channel
         *     * `zabbix` - Zabbix
         *     * `direct_paging` - Direct paging
         *     * `servicenow` - ServiceNow
         *     * `amazon_sns` - Amazon SNS
         *     * `stackdriver` - Stackdriver
         *     * `curler` - Curler
         *     * `datadog` - Datadog
         *     * `demo` - Demo
         *     * `fabric` - Fabric
         *     * `newrelic` - New Relic
         *     * `pagerduty` - Pagerduty
         *     * `pingdom` - Pingdom
         *     * `prtg` - PRTG
         *     * `sentry` - Sentry
         *     * `uptimerobot` - UptimeRobot
         *     * `jira` - Jira
         *     * `zendesk` - Zendesk
         *     * `appdynamics` - AppDynamics */
        integration?: (
          | 'alertmanager'
          | 'amazon_sns'
          | 'appdynamics'
          | 'curler'
          | 'datadog'
          | 'demo'
          | 'direct_paging'
          | 'elastalert'
          | 'fabric'
          | 'formatted_webhook'
          | 'grafana'
          | 'grafana_alerting'
          | 'heartbeat'
          | 'inbound_email'
          | 'jira'
          | 'kapacitor'
          | 'legacy_alertmanager'
          | 'legacy_grafana_alerting'
          | 'maintenance'
          | 'manual'
          | 'newrelic'
          | 'pagerduty'
          | 'pingdom'
          | 'prtg'
          | 'sentry'
          | 'servicenow'
          | 'slack_channel'
          | 'stackdriver'
          | 'uptimerobot'
          | 'webhook'
          | 'zabbix'
          | 'zendesk'
        )[];
        /** @description * `alertmanager` - Alertmanager
         *     * `legacy_alertmanager` - (Legacy) AlertManager
         *     * `grafana` - Grafana
         *     * `grafana_alerting` - Grafana Alerting
         *     * `legacy_grafana_alerting` - (Legacy) Grafana Alerting
         *     * `formatted_webhook` - Formatted webhook
         *     * `webhook` - Webhook
         *     * `kapacitor` - Kapacitor
         *     * `elastalert` - Elastalert
         *     * `heartbeat` - Heartbeat
         *     * `inbound_email` - Inbound Email
         *     * `maintenance` - Maintenance
         *     * `manual` - Manual
         *     * `slack_channel` - Slack Channel
         *     * `zabbix` - Zabbix
         *     * `direct_paging` - Direct paging
         *     * `servicenow` - ServiceNow
         *     * `amazon_sns` - Amazon SNS
         *     * `stackdriver` - Stackdriver
         *     * `curler` - Curler
         *     * `datadog` - Datadog
         *     * `demo` - Demo
         *     * `fabric` - Fabric
         *     * `newrelic` - New Relic
         *     * `pagerduty` - Pagerduty
         *     * `pingdom` - Pingdom
         *     * `prtg` - PRTG
         *     * `sentry` - Sentry
         *     * `uptimerobot` - UptimeRobot
         *     * `jira` - Jira
         *     * `zendesk` - Zendesk
         *     * `appdynamics` - AppDynamics */
        integration_ne?: (
          | 'alertmanager'
          | 'amazon_sns'
          | 'appdynamics'
          | 'curler'
          | 'datadog'
          | 'demo'
          | 'direct_paging'
          | 'elastalert'
          | 'fabric'
          | 'formatted_webhook'
          | 'grafana'
          | 'grafana_alerting'
          | 'heartbeat'
          | 'inbound_email'
          | 'jira'
          | 'kapacitor'
          | 'legacy_alertmanager'
          | 'legacy_grafana_alerting'
          | 'maintenance'
          | 'manual'
          | 'newrelic'
          | 'pagerduty'
          | 'pingdom'
          | 'prtg'
          | 'sentry'
          | 'servicenow'
          | 'slack_channel'
          | 'stackdriver'
          | 'uptimerobot'
          | 'webhook'
          | 'zabbix'
          | 'zendesk'
        )[];
        /** @description * `0` - Debug
         *     * `1` - Maintenance */
        maintenance_mode?: (0 | 1)[];
        /** @description A page number within the paginated result set. */
        page?: number;
        /** @description Number of results to return per page. */
        perpage?: number;
        /** @description A search term. */
        search?: string;
        team?: string[];
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['PaginatedAlertReceiveChannelPolymorphicList'];
        };
      };
    };
  };
  alert_receive_channels_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelCreate'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelCreate'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelCreate'];
      };
    };
    responses: {
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelCreate'];
        };
      };
    };
  };
  alert_receive_channels_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannel'];
        };
      };
    };
  };
  alert_receive_channels_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelUpdate'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelUpdate'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelUpdate'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelUpdate'];
        };
      };
    };
  };
  alert_receive_channels_destroy: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_partial_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['PatchedAlertReceiveChannelUpdate'];
        'application/x-www-form-urlencoded': components['schemas']['PatchedAlertReceiveChannelUpdate'];
        'multipart/form-data': components['schemas']['PatchedAlertReceiveChannelUpdate'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelUpdate'];
        };
      };
    };
  };
  alert_receive_channels_api_token_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_api_token_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['IntegrationTokenPostResponse'];
        };
      };
    };
  };
  alert_receive_channels_change_team_update: {
    parameters: {
      query: {
        team_id: string;
      };
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_connect_contact_point_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelConnectContactPoint'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelConnectContactPoint'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelConnectContactPoint'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_connected_alert_receive_channels_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelConnection'];
        };
      };
    };
  };
  alert_receive_channels_connected_alert_receive_channels_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelNewConnection'][];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelNewConnection'][];
        'multipart/form-data': components['schemas']['AlertReceiveChannelNewConnection'][];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelConnection'];
        };
      };
    };
  };
  alert_receive_channels_connected_alert_receive_channels_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        connected_alert_receive_channel_id: string;
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelConnectedChannel'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelConnectedChannel'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelConnectedChannel'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelConnectedChannel'];
        };
      };
    };
  };
  alert_receive_channels_connected_alert_receive_channels_destroy: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        connected_alert_receive_channel_id: string;
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_connected_contact_points_list: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelConnectedContactPoints'][];
        };
      };
    };
  };
  alert_receive_channels_counters_per_integration_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': {
            [key: string]:
              | {
                  alerts_count: number;
                  alert_groups_count: number;
                }
              | undefined;
          };
        };
      };
    };
  };
  alert_receive_channels_create_contact_point_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelCreateContactPoint'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelCreateContactPoint'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelCreateContactPoint'];
      };
    };
    responses: {
      /** @description No response body */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_disconnect_contact_point_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelDisconnectContactPoint'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelDisconnectContactPoint'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelDisconnectContactPoint'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_migrate_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_preview_template_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['PreviewTemplateRequest'];
        'application/x-www-form-urlencoded': components['schemas']['PreviewTemplateRequest'];
        'multipart/form-data': components['schemas']['PreviewTemplateRequest'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['PreviewTemplateResponse'];
        };
      };
    };
  };
  alert_receive_channels_send_demo_alert_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelSendDemoAlert'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelSendDemoAlert'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelSendDemoAlert'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_start_maintenance_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelStartMaintenance'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelStartMaintenance'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelStartMaintenance'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_status_options_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': string[][];
        };
      };
    };
  };
  alert_receive_channels_stop_maintenance_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_test_connection_create_2: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannelUpdate'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannelUpdate'];
        'multipart/form-data': components['schemas']['AlertReceiveChannelUpdate'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_webhooks_list: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['Webhook'][];
        };
      };
    };
  };
  alert_receive_channels_webhooks_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['Webhook'];
        'application/x-www-form-urlencoded': components['schemas']['Webhook'];
        'multipart/form-data': components['schemas']['Webhook'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['Webhook'];
        };
      };
    };
  };
  alert_receive_channels_webhooks_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
        webhook_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['Webhook'];
        'application/x-www-form-urlencoded': components['schemas']['Webhook'];
        'multipart/form-data': components['schemas']['Webhook'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['Webhook'];
        };
      };
    };
  };
  alert_receive_channels_webhooks_destroy: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert receive channel. */
        id: string;
        webhook_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_contact_points_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelContactPoints'][];
        };
      };
    };
  };
  alert_receive_channels_counters_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': {
            [key: string]:
              | {
                  alerts_count: number;
                  alert_groups_count: number;
                }
              | undefined;
          };
        };
      };
    };
  };
  alert_receive_channels_filters_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelFilters'][];
        };
      };
    };
  };
  alert_receive_channels_integration_options_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertReceiveChannelIntegrationOptions'][];
        };
      };
    };
  };
  alert_receive_channels_test_connection_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertReceiveChannel'];
        'application/x-www-form-urlencoded': components['schemas']['AlertReceiveChannel'];
        'multipart/form-data': components['schemas']['AlertReceiveChannel'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alert_receive_channels_validate_name_retrieve: {
    parameters: {
      query: {
        verbal_name: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description No response body */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alertgroups_list: {
    parameters: {
      query?: {
        acknowledged_by?: string[];
        /** @description The pagination cursor value. */
        cursor?: string;
        escalation_chain?: string[];
        integration?: string[];
        invitees_are?: string[];
        involved_users_are?: string[];
        is_root?: boolean;
        mine?: boolean;
        /** @description Number of results to return per page. */
        perpage?: number;
        resolved_at?: string;
        resolved_by?: string[];
        /** @description A search term. */
        search?: string;
        silenced_by?: string[];
        started_at?: string;
        /** @description * `0` - New
         *     * `1` - Acknowledged
         *     * `2` - Resolved
         *     * `3` - Silenced */
        status?: (0 | 1 | 2 | 3)[];
        with_resolution_note?: boolean;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['PaginatedAlertGroupListList'];
        };
      };
    };
  };
  alertgroups_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_destroy: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alertgroups_acknowledge_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_attach_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroupAttach'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroupAttach'];
        'multipart/form-data': components['schemas']['AlertGroupAttach'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_escalation_snapshot_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alertgroups_preview_template_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['PreviewTemplateRequest'];
        'application/x-www-form-urlencoded': components['schemas']['PreviewTemplateRequest'];
        'multipart/form-data': components['schemas']['PreviewTemplateRequest'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['PreviewTemplateResponse'];
        };
      };
    };
  };
  alertgroups_resolve_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['AlertGroupResolve'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroupResolve'];
        'multipart/form-data': components['schemas']['AlertGroupResolve'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_silence_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroupSilence'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroupSilence'];
        'multipart/form-data': components['schemas']['AlertGroupSilence'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_unacknowledge_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_unattach_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_unpage_user_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroupUnpageUser'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroupUnpageUser'];
        'multipart/form-data': components['schemas']['AlertGroupUnpageUser'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_unresolve_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_unsilence_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this alert group. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_bulk_action_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroupBulkActionRequest'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroupBulkActionRequest'];
        'multipart/form-data': components['schemas']['AlertGroupBulkActionRequest'];
      };
    };
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  alertgroups_bulk_action_options_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroupBulkActionOptions'][];
        };
      };
    };
  };
  alertgroups_filters_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroupFilters'][];
        };
      };
    };
  };
  alertgroups_labels_id_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  alertgroups_labels_keys_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelKey'][];
        };
      };
    };
  };
  alertgroups_silence_options_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroupSilenceOptions'][];
        };
      };
    };
  };
  alertgroups_stats_retrieve: {
    parameters: {
      query?: {
        acknowledged_by?: string[];
        escalation_chain?: string[];
        integration?: string[];
        invitees_are?: string[];
        involved_users_are?: string[];
        is_root?: boolean;
        mine?: boolean;
        resolved_at?: string;
        resolved_by?: string[];
        /** @description A search term. */
        search?: string;
        silenced_by?: string[];
        started_at?: string;
        /** @description * `0` - New
         *     * `1` - Acknowledged
         *     * `2` - Resolved
         *     * `3` - Silenced */
        status?: (0 | 1 | 2 | 3)[];
        with_resolution_note?: boolean;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['AlertGroupStats'];
        };
      };
    };
  };
  complete_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        backend: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  disconnect_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        backend: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  features_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': (
            | 'msteams'
            | 'slack'
            | 'telegram'
            | 'live_settings'
            | 'grafana_cloud_notifications'
            | 'grafana_cloud_connection'
            | 'grafana_alerting_v2'
            | 'labels'
            | 'google_oauth2'
          )[];
        };
      };
    };
  };
  labels_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['LabelCreate'][];
        'application/x-www-form-urlencoded': components['schemas']['LabelCreate'][];
        'multipart/form-data': components['schemas']['LabelCreate'][];
      };
    };
    responses: {
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  labels_id_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  labels_id_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['LabelRepr'];
        'application/x-www-form-urlencoded': components['schemas']['LabelRepr'];
        'multipart/form-data': components['schemas']['LabelRepr'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  labels_id_values_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['LabelRepr'];
        'application/x-www-form-urlencoded': components['schemas']['LabelRepr'];
        'multipart/form-data': components['schemas']['LabelRepr'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  labels_id_values_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
        value_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelValue'];
        };
      };
    };
  };
  labels_id_values_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key_id: string;
        value_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['LabelRepr'];
        'application/x-www-form-urlencoded': components['schemas']['LabelRepr'];
        'multipart/form-data': components['schemas']['LabelRepr'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelOption'];
        };
      };
    };
  };
  labels_keys_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['LabelKey'][];
        };
      };
    };
  };
  login_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        backend: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  login_retrieve_2: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        backend: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_list: {
    parameters: {
      query?: {
        email?: string;
        /** @description A page number within the paginated result set. */
        page?: number;
        /** @description * `grafana-oncall-app.alert-groups:direct-paging` - ALERT_GROUPS_DIRECT_PAGING
         *     * `grafana-oncall-app.alert-groups:read` - ALERT_GROUPS_READ
         *     * `grafana-oncall-app.alert-groups:write` - ALERT_GROUPS_WRITE
         *     * `grafana-oncall-app.api-keys:read` - API_KEYS_READ
         *     * `grafana-oncall-app.api-keys:write` - API_KEYS_WRITE
         *     * `grafana-oncall-app.chatops:read` - CHATOPS_READ
         *     * `grafana-oncall-app.chatops:update-settings` - CHATOPS_UPDATE_SETTINGS
         *     * `grafana-oncall-app.chatops:write` - CHATOPS_WRITE
         *     * `grafana-oncall-app.escalation-chains:read` - ESCALATION_CHAINS_READ
         *     * `grafana-oncall-app.escalation-chains:write` - ESCALATION_CHAINS_WRITE
         *     * `grafana-oncall-app.integrations:read` - INTEGRATIONS_READ
         *     * `grafana-oncall-app.integrations:test` - INTEGRATIONS_TEST
         *     * `grafana-oncall-app.integrations:write` - INTEGRATIONS_WRITE
         *     * `grafana-oncall-app.maintenance:read` - MAINTENANCE_READ
         *     * `grafana-oncall-app.maintenance:write` - MAINTENANCE_WRITE
         *     * `grafana-oncall-app.notifications:read` - NOTIFICATIONS_READ
         *     * `grafana-oncall-app.notification-settings:read` - NOTIFICATION_SETTINGS_READ
         *     * `grafana-oncall-app.notification-settings:write` - NOTIFICATION_SETTINGS_WRITE
         *     * `grafana-oncall-app.other-settings:read` - OTHER_SETTINGS_READ
         *     * `grafana-oncall-app.other-settings:write` - OTHER_SETTINGS_WRITE
         *     * `grafana-oncall-app.outgoing-webhooks:read` - OUTGOING_WEBHOOKS_READ
         *     * `grafana-oncall-app.outgoing-webhooks:write` - OUTGOING_WEBHOOKS_WRITE
         *     * `grafana-oncall-app.schedules:export` - SCHEDULES_EXPORT
         *     * `grafana-oncall-app.schedules:read` - SCHEDULES_READ
         *     * `grafana-oncall-app.schedules:write` - SCHEDULES_WRITE
         *     * `grafana-oncall-app.user-settings:admin` - USER_SETTINGS_ADMIN
         *     * `grafana-oncall-app.user-settings:read` - USER_SETTINGS_READ
         *     * `grafana-oncall-app.user-settings:write` - USER_SETTINGS_WRITE */
        permission?:
          | 'grafana-oncall-app.alert-groups:direct-paging'
          | 'grafana-oncall-app.alert-groups:read'
          | 'grafana-oncall-app.alert-groups:write'
          | 'grafana-oncall-app.api-keys:read'
          | 'grafana-oncall-app.api-keys:write'
          | 'grafana-oncall-app.chatops:read'
          | 'grafana-oncall-app.chatops:update-settings'
          | 'grafana-oncall-app.chatops:write'
          | 'grafana-oncall-app.escalation-chains:read'
          | 'grafana-oncall-app.escalation-chains:write'
          | 'grafana-oncall-app.integrations:read'
          | 'grafana-oncall-app.integrations:test'
          | 'grafana-oncall-app.integrations:write'
          | 'grafana-oncall-app.maintenance:read'
          | 'grafana-oncall-app.maintenance:write'
          | 'grafana-oncall-app.notification-settings:read'
          | 'grafana-oncall-app.notification-settings:write'
          | 'grafana-oncall-app.notifications:read'
          | 'grafana-oncall-app.other-settings:read'
          | 'grafana-oncall-app.other-settings:write'
          | 'grafana-oncall-app.outgoing-webhooks:read'
          | 'grafana-oncall-app.outgoing-webhooks:write'
          | 'grafana-oncall-app.schedules:export'
          | 'grafana-oncall-app.schedules:read'
          | 'grafana-oncall-app.schedules:write'
          | 'grafana-oncall-app.user-settings:admin'
          | 'grafana-oncall-app.user-settings:read'
          | 'grafana-oncall-app.user-settings:write';
        /** @description Number of results to return per page. */
        perpage?: number;
        /** @description * `0` - ADMIN
         *     * `1` - EDITOR
         *     * `2` - VIEWER
         *     * `3` - NONE */
        roles?: (0 | 1 | 2 | 3)[];
        /** @description A search term. */
        search?: string;
        team?: string[];
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['PaginatedUserPolymorphicList'];
        };
      };
    };
  };
  users_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['User'];
        };
      };
    };
  };
  users_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['User'];
        'application/x-www-form-urlencoded': components['schemas']['User'];
        'multipart/form-data': components['schemas']['User'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['User'];
        };
      };
    };
  };
  users_partial_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: {
      content: {
        'application/json': components['schemas']['PatchedUser'];
        'application/x-www-form-urlencoded': components['schemas']['PatchedUser'];
        'multipart/form-data': components['schemas']['PatchedUser'];
      };
    };
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['User'];
        };
      };
    };
  };
  users_export_token_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['UserExportTokenGetResponse'];
        };
      };
    };
  };
  users_export_token_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['UserExportTokenPostResponse'];
        };
      };
    };
  };
  users_export_token_destroy: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_forget_number_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_get_backend_verification_code_retrieve: {
    parameters: {
      query: {
        backend: string;
      };
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_get_telegram_verification_code_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': components['schemas']['UserGetTelegramVerificationCode'];
        };
      };
    };
  };
  users_get_verification_call_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_get_verification_code_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_make_test_call_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_send_test_push_create: {
    parameters: {
      query?: {
        critical?: boolean;
      };
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_send_test_sms_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_unlink_backend_create: {
    parameters: {
      query: {
        backend: string;
      };
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_unlink_slack_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_unlink_telegram_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_upcoming_shifts_retrieve: {
    parameters: {
      query?: {
        days?: number;
      };
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': {
            schedule_id: string;
            schedule_name: string;
            is_oncall: boolean;
            current_shift: {
              all_day: boolean;
              /** Format: date-time */
              start: string;
              /** Format: date-time */
              end: string;
              users: {
                display_name: string;
                pk: string;
                email: string;
                avatar_full: string;
                swap_request: {
                  pk: string;
                  user: {
                    display_name: string;
                    pk: string;
                    email: string;
                    avatar_full: string;
                  } | null;
                } | null;
              }[];
              missing_users: string[];
              priority_level: number | null;
              source: string | null;
              calendar_type: number | null;
              is_empty: boolean;
              is_gap: boolean;
              is_override: boolean;
              shift: {
                pk: string;
              };
            } | null;
            next_shift: {
              all_day: boolean;
              /** Format: date-time */
              start: string;
              /** Format: date-time */
              end: string;
              users: {
                display_name: string;
                pk: string;
                email: string;
                avatar_full: string;
                swap_request: {
                  pk: string;
                  user: {
                    display_name: string;
                    pk: string;
                    email: string;
                    avatar_full: string;
                  } | null;
                } | null;
              }[];
              missing_users: string[];
              priority_level: number | null;
              source: string | null;
              calendar_type: number | null;
              is_empty: boolean;
              is_gap: boolean;
              is_override: boolean;
              shift: {
                pk: string;
              };
            } | null;
          }[];
        };
      };
    };
  };
  users_verify_number_update: {
    parameters: {
      query: {
        token: string;
      };
      header?: never;
      path: {
        /** @description A string identifying this user. */
        id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description No response body */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  users_timezone_options_retrieve: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          'application/json': string[];
        };
      };
    };
  };
}
