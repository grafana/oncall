import { ThresholdsMode } from '@grafana/data';
import { SceneDataTransformer, SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

import { InsightsConfig } from 'pages/insights/Insights.types';

export default function getTotalAlertGroupsByStateScene({ datasource }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        disableTextWrap: false,
        editorMode: 'code',
        excludeNullMetadata: false,
        expr: 'sum by (state) (avg without(pod, stack) ($alert_groups_total{slug=~"$stack", team=~"$team", integration=~"$integration"}))',
        fullMetaSearch: false,
        legendFormat: '__auto',
        range: true,
        refId: 'A',
        useBackend: false,
      },
    ],
  });

  const transformedData = new SceneDataTransformer({
    $data: query,
    transformations: [
      {
        id: 'joinByLabels',
        options: {
          value: 'state',
        },
      },
      {
        id: 'organize',
        options: {
          excludeByName: {},
          indexByName: {
            acknowledged: 1,
            firing: 0,
            resolved: 2,
            silenced: 3,
          },
          renameByName: {},
        },
      },
    ],
  });

  return new SceneFlexItem({
    $data: transformedData,
    body: new VizPanel({
      title: 'Total alert groups by state',
      pluginId: 'bargauge',
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
                color: 'green',
                value: null,
              },
            ],
          },
        },
        overrides: [
          {
            matcher: {
              id: 'byName',
              options: 'firing',
            },
            properties: [
              {
                id: 'color',
                value: {
                  fixedColor: 'red',
                  mode: 'fixed',
                },
              },
            ],
          },
          {
            matcher: {
              id: 'byName',
              options: 'acknowledged',
            },
            properties: [
              {
                id: 'color',
                value: {
                  fixedColor: 'dark-yellow',
                  mode: 'fixed',
                },
              },
            ],
          },
          {
            matcher: {
              id: 'byName',
              options: 'silenced',
            },
            properties: [
              {
                id: 'color',
                value: {
                  mode: 'fixed',
                },
              },
            ],
          },
        ],
      },
      options: {
        displayMode: 'gradient',
        minVizHeight: 10,
        minVizWidth: 0,
        orientation: 'vertical',
        reduceOptions: {
          calcs: ['lastNotNull'],
          fields: '',
          values: false,
        },
        showUnfilled: true,
        valueMode: 'color',
      },
      pluginVersion: '9.5.2',
    }),
  });
}
