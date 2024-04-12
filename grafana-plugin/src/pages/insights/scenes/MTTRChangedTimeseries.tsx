import { ThresholdsMode } from '@grafana/data';
import { SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export function getMTTRChangedTimeseriesScene({ datasource, stack }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: `avg(sum($alert_groups_response_time_seconds_sum{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}) / sum($alert_groups_response_time_seconds_count{slug=~"${stack}", team=~"$team", integration=~"$integration", service_name=~"$service_name"}))`,
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
      pluginId: 'timeseries',
      fieldConfig: {
        defaults: {
          color: {
            fixedColor: 'green',
            mode: 'fixed',
            seriesBy: 'min',
          },
          custom: {
            axisCenteredZero: false,
            axisColorMode: 'text',
            axisLabel: '',
            axisPlacement: 'auto',
            barAlignment: 0,
            drawStyle: 'line',
            fillOpacity: 54,
            gradientMode: 'opacity',
            hideFrom: {
              legend: false,
              tooltip: false,
              viz: false,
            },
            lineInterpolation: 'linear',
            lineStyle: {
              fill: 'solid',
            },
            lineWidth: 1,
            pointSize: 5,
            scaleDistribution: {
              type: 'linear',
            },
            showPoints: 'auto',
            spanNulls: true,
            stacking: {
              group: 'A',
              mode: 'none',
            },
            thresholdsStyle: {
              mode: 'off',
            },
          },
          mappings: [],
          thresholds: {
            mode: ThresholdsMode.Absolute,
            steps: [
              {
                color: 'text',
                value: 0,
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
        legend: {
          displayMode: 'list',
          placement: 'bottom',
          showLegend: false,
        },
        tooltip: {
          mode: 'single',
          sort: 'none',
        },
      },
    }),
  });
}
