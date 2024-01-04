import { ThresholdsMode } from '@grafana/data';
import { SceneDataTransformer, SceneFlexItem, SceneQueryRunner, VizPanel } from '@grafana/scenes';

export default function getMTTRByIntegrationScene({ datasource }: InsightsConfig) {
  const query = new SceneQueryRunner({
    datasource,
    queries: [
      {
        editorMode: 'code',
        exemplar: false,
        expr: 'sort_desc(avg_over_time((sum by (integration)($alert_groups_response_time_seconds_sum{slug=~"$instance", team=~"$team", integration=~"$integration"}) / sum by (integration)($alert_groups_response_time_seconds_count{slug=~"$instance", team=~"$team", integration=~"$integration"}))[$__range:]))',
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
            cluster: true,
            container: true,
            id: true,
            instance: true,
            job: true,
            namespace: true,
            org_id: true,
            pod: true,
            slug: true,
            team: true,
          },
          indexByName: {},
          renameByName: {
            Metric: 'Integration',
            Value: 'MTTR',
            integration: 'Integration',
          },
        },
      },
    ],
  });

  return new SceneFlexItem({
    $data: transformedData,
    body: new VizPanel({
      title: 'Mean time to respond (MTTR) by Integration',
      pluginId: 'table',
      fieldConfig: {
        defaults: {
          color: {
            mode: 'continuous-GrYlRd',
          },
          custom: {
            align: 'auto',
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
                value: 0,
              },
              {
                color: 'red',
                value: 5400,
              },
            ],
          },
          unit: 's',
        },
        overrides: [
          {
            matcher: {
              id: 'byName',
              options: 'Integration',
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
