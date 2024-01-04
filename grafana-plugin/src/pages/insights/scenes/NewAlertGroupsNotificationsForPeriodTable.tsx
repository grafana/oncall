import { ThresholdsMode } from '@grafana/data';
import { SceneDataTransformer, SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';
import { InsightsConfig } from '../Insights.types';

export default function getNewAlertGroupsNotificationsForPeriodTableScene({ datasource }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: 'sort_desc(increase(max_over_time(sum by (username) (avg without(pod, instance) ($user_was_notified_of_alert_groups_total{slug=~"$instance"}))[1h:])[$__range:]))',
        format: 'table',
        instant: true,
        legendFormat: '__auto',
        range: false,
        refId: 'A',
      },
    ],
  });

  const transformedData = new SceneDataTransformer({
    $data: query,
    transformations: [
      {
        id: 'seriesToRows',
        options: {},
      },
      {
        id: 'organize',
        options: {
          excludeByName: {
            Time: true,
            username: false,
          },
          indexByName: {},
          renameByName: {
            Metric: 'Integration',
            Value: 'Alert groups',
            team: 'Team',
            username: 'Username',
          },
        },
      },
    ],
  });

  return new SceneFlexItem({
    $data: transformedData,
    body: new VizPanel({
      title: 'New alert groups notifications for period',
      pluginId: 'table',
      fieldConfig: {
        defaults: {
          color: {
            mode: 'thresholds',
          },
          custom: {
            align: 'auto',
            cellOptions: {
              type: 'gauge',
            },
            filterable: false,
            inspect: false,
          },
          decimals: 0,
          mappings: [],
          thresholds: {
            mode: ThresholdsMode.Absolute,
            steps: [
              {
                color: 'green',
                value: null,
              },
            ],
          },
          unit: 'none',
        },
        overrides: [
          {
            matcher: {
              id: 'byName',
              options: 'Username',
            },
            properties: [
              {
                id: 'custom.cellOptions',
                value: {
                  type: 'auto',
                },
              },
              {
                id: 'custom.width',
                value: 300,
              },
            ],
          },
        ],
      },
      options: {
        cellHeight: 'sm',
        footer: {
          countRows: false,
          fields: '',
          reducer: ['sum'],
          show: false,
        },
        showHeader: true,
      },
    }),
  });
}
