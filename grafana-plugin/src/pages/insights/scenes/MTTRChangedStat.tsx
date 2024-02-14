import { ThresholdsMode } from '@grafana/data';
import { SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export function getMTTRChanged({ datasource, stack }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        // expr: `avg(sum($alert_groups_response_time_seconds_sum{slug=~"${stack}", team=~"$team", integration=~"$integration"}) / sum($alert_groups_response_time_seconds_count{slug=~"${stack}", team=~"$team", integration=~"$integration"}))`,
        expr: `avg(sum($alert_groups_response_time_seconds_sum{slug=~"${stack}", team=~"$team", integration=~"$integration"}) / sum($alert_groups_response_time_seconds_count{slug=~"${stack}", team=~"$team", integration=~"$integration"}))`,
        instant: false,
        legendFormat: '__auto',
        range: true,
        refId: 'A',
      },
    ],
  });

  return new SceneFlexItem({
    $data: query,
    body: new VizPanel({
      title: 'Mean time to respond (MTTR) changed',
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
        },
        overrides: [],
      },
      options: {
        colorMode: 'value',
        graphMode: 'none',
        justifyMode: 'center',
        orientation: 'auto',
        reduceOptions: {
          calcs: ['diff'],
          fields: '',
          values: false,
        },
        textMode: 'auto',
      },
    }),
  });
}
