import type { CustomApiSchemas } from './types-generator/custom-schemas';

export interface paths {
  '/alertgroups/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** @description Fetch a list of alert groups */
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
    /** @description Fetch a single alert group */
    get: operations['alertgroups_retrieve'];
    put?: never;
    post?: never;
    /** @description Delete an alert group */
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
  '/alertgroups/{id}/preview_template/': {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** @description Preview a template for an alert group */
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
    get: operations['alertgroups_bulk_action_options_retrieve'];
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
    get: operations['alertgroups_filters_retrieve'];
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
    /** @description Key with the list of values */
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
    /** @description Value name */
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
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    Alert: {
      readonly id: string;
      /** Format: uri */
      link_to_upstream_details?: string | null;
      readonly render_for_web: string;
      /** Format: date-time */
      readonly created_at: string;
    };
    AlertGroup: {
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
      readonly render_for_web: components['schemas']['render_for_web'];
      dependent_alert_groups: components['schemas']['ShortAlertGroup'][];
      root_alert_group: components['schemas']['ShortAlertGroup'];
      readonly status: string;
      /** @description Generate a link for AlertGroup to declare Grafana Incident by click */
      readonly declare_incident_link: string;
      team: string | null;
      grafana_incident_id?: string | null;
      readonly labels: components['schemas']['AlertGroupLabel'][];
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
      readonly permalinks: {
        slack: string | null;
        telegram: string | null;
        web: string;
      };
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
      readonly render_for_web: components['schemas']['render_for_web'];
      dependent_alert_groups: components['schemas']['ShortAlertGroup'][];
      root_alert_group: components['schemas']['ShortAlertGroup'];
      readonly status: string;
      /** @description Generate a link for AlertGroup to declare Grafana Incident by click */
      readonly declare_incident_link: string;
      team: string | null;
      grafana_incident_id?: string | null;
      readonly labels: components['schemas']['AlertGroupLabel'][];
    };
    AlertGroupStats: {
      count: number;
    };
    FastAlertReceiveChannel: {
      readonly id: string;
      readonly integration: string;
      verbal_name?: string | null;
      readonly deleted: boolean;
    };
    FastUser: {
      pk: string;
      readonly username: string;
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
    };
    LabelKeyValues: {
      key: components['schemas']['LabelKey'];
      values: components['schemas']['LabelValue'][];
    };
    LabelRepr: {
      name: string;
    };
    LabelValue: {
      id: string;
      name: string;
    };
    PaginatedAlertGroupListList: {
      next?: string | null;
      previous?: string | null;
      results?: components['schemas']['AlertGroupList'][];
    };
    Paginatedsilence_optionsList: {
      next?: string | null;
      previous?: string | null;
      results?: components['schemas']['silence_options'][];
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
    ShortAlertGroup: {
      readonly pk: string;
      readonly render_for_web: components['schemas']['render_for_web'];
      alert_receive_channel: components['schemas']['FastAlertReceiveChannel'];
      readonly inside_organization_number: number;
    };
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
    render_for_web: {
      title: string;
      message: string;
      image_url: string;
      source_link: string;
    };
    silence_options: {
      value: string;
      display_name: string;
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
  alertgroups_list: {
    parameters: {
      query?: {
        /** @description The pagination cursor value. */
        cursor?: string;
        /** @description Number of results to return per page. */
        perpage?: number;
        /** @description A search term. */
        search?: string;
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
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_attach_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_preview_template_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_resolve_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_unattach_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_unpage_user_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_unsilence_create: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_bulk_action_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        'application/json': components['schemas']['AlertGroup'];
        'application/x-www-form-urlencoded': components['schemas']['AlertGroup'];
        'multipart/form-data': components['schemas']['AlertGroup'];
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
  alertgroups_bulk_action_options_retrieve: {
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
          'application/json': components['schemas']['AlertGroup'];
        };
      };
    };
  };
  alertgroups_filters_retrieve: {
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
          'application/json': components['schemas']['AlertGroup'];
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
          'application/json': components['schemas']['LabelKeyValues'];
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
      query?: {
        /** @description The pagination cursor value. */
        cursor?: string;
        /** @description Number of results to return per page. */
        perpage?: number;
        /** @description A search term. */
        search?: string;
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
          'application/json': components['schemas']['Paginatedsilence_optionsList'];
        };
      };
    };
  };
  alertgroups_stats_retrieve: {
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
          'application/json': components['schemas']['AlertGroupStats'];
        };
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
          'application/json': {
            [key: string]: unknown;
          };
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
          'application/json': components['schemas']['LabelKeyValues'];
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
          'application/json': components['schemas']['LabelKeyValues'];
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
          'application/json': components['schemas']['LabelKeyValues'];
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
          'application/json': components['schemas']['LabelKeyValues'];
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
          'application/json': components['schemas']['LabelKeyValues'];
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
}
