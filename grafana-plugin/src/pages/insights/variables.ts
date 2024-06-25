import { DataSourceVariable, QueryVariable } from '@grafana/scenes';

import { InsightsConfig } from './Insights.types';

const DEFAULT_VARIABLE_CONFIG: Partial<ConstructorParameters<typeof QueryVariable>[0]> = {
  hide: 0,
  isMulti: true,
  options: [],
  refresh: 1,
  regex: '',
  skipUrlSync: false,
  sort: 0,
  type: 'query',
};

const getVariables = ({ isOpenSource, datasource, stack }: InsightsConfig) => ({
  // Selectable
  ...(isOpenSource
    ? {
        datasource: new DataSourceVariable({
          name: 'datasource',
          label: 'Data source',
          pluginId: 'prometheus',
          value: 'grafanacloud-usage',
        }),
      }
    : {}),
  team: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'team',
    label: 'Team',
    text: ['All'],
    value: ['$__all'],
    includeAll: true,
    allValue: `.+`,
    datasource,
    definition: `label_values(\${alert_groups_total}{slug=~"${stack}"},team)`,
    query: {
      query: `label_values(\${alert_groups_total}{slug=~"${stack}"},team)`,
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    refresh: 2,
  }),
  integration: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'integration',
    label: 'Integration',
    text: ['All'],
    value: ['$__all'],
    includeAll: true,
    allValue: `.+`,
    datasource,
    definition: `label_values(\${alert_groups_total}{team=~"$team",slug=~"${stack}"},integration)`,
    query: {
      query: `label_values(\${alert_groups_total}{team=~"$team",slug=~"${stack}"},integration)`,
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    refresh: 2,
  }),
  service_name: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'service_name',
    label: 'Service name',
    text: ['All'],
    value: ['$__all'],
    includeAll: true,
    allValue: '($^)|(.+)',
    datasource,
    definition: `label_values(\${alert_groups_total}{slug=~"${stack}",team=~"$team"},service_name)`,
    query: {
      query: `label_values(\${alert_groups_total}{slug=~"${stack}",team=~"$team"},service_name)`,
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    refresh: 2,
  }),

  // Non-selectable
  alertGroupsTotal: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'alert_groups_total',
    label: 'alert_groups_total',
    datasource,
    query: {
      query: 'metrics(alert_groups_total)',
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    text: ['oncall_alert_groups_total', 'grafanacloud_oncall_instance_alert_groups_total'],
    value: ['oncall_alert_groups_total', 'grafanacloud_oncall_instance_alert_groups_total'],
    definition: 'metrics(alert_groups_total)',
    hide: 2,
  }),
  userNotified: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'user_was_notified_of_alert_groups_total',
    label: 'user_was_notified_of_alert_groups_total',
    datasource,
    definition: 'metrics(user_was_notified_of_alert_groups_total)',
    query: {
      query: 'metrics(user_was_notified_of_alert_groups_total)',
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    hide: 2,
    refresh: 2,
  }),
  alertGroupsResponseTimeBucket: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'alert_groups_response_time_seconds_bucket',
    label: 'alert_groups_response_time_seconds_bucket',
    datasource,
    definition: 'metrics(alert_groups_response_time_seconds_bucket)',
    query: {
      query: 'metrics(alert_groups_response_time_seconds_bucket)',
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    hide: 2,
  }),
  alertGroupsResponseTimeSum: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'alert_groups_response_time_seconds_sum',
    label: 'alert_groups_response_time_seconds_sum',
    datasource,
    definition: 'metrics(alert_groups_response_time_seconds_sum)',
    query: {
      query: 'metrics(alert_groups_response_time_seconds_sum)',
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    hide: 2,
  }),
  alertGroupsResponseTimeCount: new QueryVariable({
    ...DEFAULT_VARIABLE_CONFIG,
    name: 'alert_groups_response_time_seconds_count',
    label: 'alert_groups_response_time_seconds_count',
    datasource,
    definition: 'metrics(alert_groups_response_time_seconds_count)',
    query: {
      query: 'metrics(alert_groups_response_time_seconds_count)',
      refId: 'PrometheusVariableQueryEditor-VariableQuery',
    },
    hide: 2,
  }),
});

export default getVariables;
