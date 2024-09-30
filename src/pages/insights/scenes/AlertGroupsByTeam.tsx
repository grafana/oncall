import { ThresholdsMode } from '@grafana/data';
import { SceneDataTransformer, SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export function getAlertGroupsByTeamScene({ datasource, stack }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: `sort_desc(round(delta(sum by (team)($alert_groups_total{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"})[$__range:])) >= 0)`,
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
        id: 'organize',
        options: {
          excludeByName: {
            Time: true,
          },
          indexByName: {},
          renameByName: {
            Metric: 'Integration',
            Value: 'Alert groups',
            team: 'Team',
          },
        },
      },
    ],
  });

  return new SceneFlexItem({
    $data: transformedData,
    body: new VizPanel({
      title: 'Alert groups by Team',
      pluginId: 'table',
      fieldConfig: {
        defaults: {
          color: {
            mode: 'thresholds',
          },
          custom: {
            align: 'auto',
            cellOptions: {
              mode: 'gradient',
              type: 'gauge',
              valueDisplayMode: 'color',
            },
            filterable: false,
            inspect: false,
          },
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
          decimals: 0,
        },
        overrides: [
          {
            matcher: {
              id: 'byName',
              options: 'Team',
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
        cellHeight: 'md',
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
