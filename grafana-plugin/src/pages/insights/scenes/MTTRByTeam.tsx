import { ThresholdsMode } from '@grafana/data';
import { SceneDataTransformer, SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export function getMTTRByTeamScene({ datasource, stack }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: `sort_desc(avg_over_time((sum by(team) ($alert_groups_response_time_seconds_sum{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}) / sum by(team)($alert_groups_response_time_seconds_count{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}))[$__range:]))`,
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
            Value: 'MTTR',
            team: 'Team',
          },
        },
      },
    ],
  });

  return new SceneFlexItem({
    $data: transformedData,
    body: new VizPanel({
      title: 'Mean time to respond (MTTR) by Team',
      pluginId: 'table',
      fieldConfig: {
        defaults: {
          color: {
            mode: 'continuous-GrYlRd',
          },
          custom: {
            align: 'left',
            cellOptions: {
              mode: 'gradient',
              type: 'gauge',
              valueDisplayMode: 'text',
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
              {
                color: 'red',
                value: 5400,
              },
            ],
          },
          unit: 's',
          min: 0,
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
