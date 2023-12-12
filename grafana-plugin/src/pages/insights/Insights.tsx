import React from 'react';

import {
  SceneQueryRunner,
  EmbeddedScene,
  SceneTimeRange,
  SceneFlexLayout,
  SceneFlexItem,
  PanelBuilders,
} from '@grafana/scenes';

export function getDataAndTimeRangeScene() {
  // Scene data, used by Panel A
  const queryRunner1 = new SceneQueryRunner({
    datasource: {
      type: 'prometheus',
      uid: 'grafanacloud-usage',
    },
    queries: [
      {
        refId: 'A',
        expr: 'grafanacloud_instance_alertmanager_alerts',
        format: 'table',
        instant: true,
        // refId: 'A',
        // expr: 'max_over_time(sum(avg without(pod, instance) ($alert_groups_total{slug=~"$instance", team=~"$team", integration=~"$integration"}))[1d:])',
      },
    ],
  });

  // Panel B data
  const queryRunner2 = new SceneQueryRunner({
    datasource: {
      type: 'prometheus',
      uid: 'grafanacloud-usage',
    },
    queries: [
      {
        refId: 'A',
        expr: 'avg by (job, instance, mode) (rate(node_cpu_seconds_total[5m]))',
      },
    ],
  });

  const scene = new EmbeddedScene({
    $data: queryRunner1,
    // Global time range. queryRunner1 will use this time range.
    $timeRange: new SceneTimeRange({ from: 'now-5m', to: 'now' }),
    body: new SceneFlexLayout({
      direction: 'row',
      children: [
        new SceneFlexItem({
          width: '50%',
          height: 300,
          body: PanelBuilders.timeseries().setTitle('Panel using global time range').build(),
        }),
        new SceneFlexItem({
          width: '50%',
          height: 300,
          body: PanelBuilders.timeseries()
            .setTitle('Panel using local time range')
            // Time range defined on VizPanel object. queryRunner2 will use this time range.
            .setTimeRange(new SceneTimeRange({ from: 'now-6h', to: 'now' }))
            .setData(queryRunner2)
            .build(),
        }),
      ],
    }),
  });

  return scene;
}

const Insights = () => {
  const scene = getDataAndTimeRangeScene();
  return <scene.Component model={scene} />;
};

export default Insights;
