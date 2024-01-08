import { ThresholdsMode } from '@grafana/data';
import { SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export default function getMTTRScene({ datasource }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: 'avg_over_time((sum($alert_groups_response_time_seconds_sum{slug=~"$instance", team=~"$team", integration=~"$integration"}) / sum($alert_groups_response_time_seconds_count{slug=~"$instance", team=~"$team", integration=~"$integration"}))[$__range:])',
        instant: true,
        legendFormat: '__auto',
        range: false,
        refId: 'A',
      },
    ],
  });

  return new SceneFlexItem({
    $data: query,
    body: new VizPanel({
      title: 'Mean time to respond (MTTR)',
      description: 'Mean time between the start and first action of all alert groups for the last 7 days',
      pluginId: 'stat',
      fieldConfig: {
        defaults: {
          color: {
            mode: 'thresholds',
          },
          mappings: [],
          thresholds: {
            mode: ThresholdsMode.Absolute,
            steps: [
              {
                color: 'text',
                value: null,
              },
            ],
          },
          unit: 's',
        },
        overrides: [
          {
            matcher: {
              id: 'byName',
              options: 'Value',
            },
            properties: [
              {
                id: 'displayName',
                value: 'MTTR',
              },
            ],
          },
        ],
      },
      options: {
        colorMode: 'value',
        graphMode: 'none',
        justifyMode: 'center',
        orientation: 'auto',
        reduceOptions: {
          calcs: ['lastNotNull'],
          fields: '',
          values: false,
        },
        textMode: 'auto',
      },
    }),
  });
}
