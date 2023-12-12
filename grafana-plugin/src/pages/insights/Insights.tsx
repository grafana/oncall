import React from 'react';

import {
  EmbeddedScene,
  SceneTimeRange,
  SceneFlexLayout,
  SceneControlsSpacer,
  SceneRefreshPicker,
  SceneTimePicker,
  SceneVariableSet,
  VariableValueSelectors,
  NestedScene,
} from '@grafana/scenes';

import { getNewAlertGroupsDuringTimePeriodScene } from './scenes/NewAlertGroupsDuringTimePeriod';
import { getTotalAlertGroupsScene } from './scenes/TotalAlertGroups';
import { getTotalAlertGroupsByStateScene } from './scenes/TotalAlertGroupsByState';
import VARIABLES from './variables';

const rootScene = new EmbeddedScene({
  $timeRange: new SceneTimeRange({ from: 'now-7d', to: 'now' }),
  $variables: new SceneVariableSet({
    variables: VARIABLES,
  }),
  controls: [
    new VariableValueSelectors({}),
    new SceneControlsSpacer(),
    new SceneTimePicker({}),
    new SceneRefreshPicker({}),
  ],
  body: new SceneFlexLayout({
    children: [
      new NestedScene({
        title: 'Overview',
        canCollapse: true,
        isCollapsed: false,
        body: new SceneFlexLayout({
          direction: 'column',
          children: [
            new SceneFlexLayout({
              height: 200,
              children: [getTotalAlertGroupsScene(), getTotalAlertGroupsByStateScene()],
            }),
            new SceneFlexLayout({
              height: 400,
              children: [getNewAlertGroupsDuringTimePeriodScene()],
            }),
          ],
        }),
      }),
    ],
  }),
});

const Insights = () => <rootScene.Component model={rootScene} />;

export default Insights;
