import { ThresholdsMode } from '@grafana/data';
import { SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export function getMTTRAverage({ datasource, stack }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: `avg_over_time((sum($alert_groups_response_time_seconds_sum{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}) / sum($alert_groups_response_time_seconds_count{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}))[$__range:])`,
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
      title: 'Mean time to respond (MTTR) average',
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
                color: 'blue',
                value: null,
              },
              {
                color: 'green',
                value: -10000000,
              },
              {
                color: 'super-light-yellow',
                value: 0,
              },
            ],
          },
          unit: 's',
          min: 0,
        },
        overrides: [],
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
