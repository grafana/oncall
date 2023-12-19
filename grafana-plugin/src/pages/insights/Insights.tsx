import React, { useMemo } from 'react';

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
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';

import { InsightsConfig } from './Insights.types';
import getAlertGroupsByIntegrationScene from './scenes/AlertGroupsByIntegration';
import getAlertGroupsByTeamScene from './scenes/AlertGroupsByTeam';
import getMTTRScene from './scenes/MTTR';
import getMTTRByIntegrationScene from './scenes/MTTRByIntegration';
import getMTTRByTeamScene from './scenes/MTTRByTeam';
import getMTTRChangedForPeriodStatScene from './scenes/MTTRChangedForPeriodStat';
import getMTTRChangedForPeriodTimeseriesScene from './scenes/MTTRChangedForPeriodTimeseries';
import getNewAlertGroupsDuringTimePeriodScene from './scenes/NewAlertGroupsDuringTimePeriod';
import getNewAlertGroupsForSelectedPeriodScene from './scenes/NewAlertGroupsForSelectedPeriod';
import getNewAlertGroupsNotificationsDuringTimePeriodScene from './scenes/NewAlertGroupsNotificationsDuringTimePeriod';
import getNewAlertGroupsNotificationsForPeriodTableScene from './scenes/NewAlertGroupsNotificationsForPeriodTable';
import getNewAlertGroupsNotificationsInTotalScene from './scenes/NewAlertGroupsNotificationsInTotal';
import getTotalAlertGroupsScene from './scenes/TotalAlertGroups';
import getTotalAlertGroupsByStateScene from './scenes/TotalAlertGroupsByState';
import getVariables from './variables';

const Insights = observer(() => {
  const { isOpenSource } = useStore();

  const rootScene = useMemo(() => getRootScene({ isOpenSource }), [isOpenSource]);

  return <rootScene.Component model={rootScene} />;
});

const getRootScene = (config: InsightsConfig) =>
  new EmbeddedScene({
    $timeRange: new SceneTimeRange({ from: 'now-7d', to: 'now' }),
    $variables: new SceneVariableSet({
      variables: getVariables(config),
    }),
    controls: [
      new VariableValueSelectors({}),
      new SceneControlsSpacer(),
      new SceneTimePicker({}),
      new SceneRefreshPicker({}),
    ],
    body: new SceneFlexLayout({
      direction: 'column',
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
                children: [
                  getTotalAlertGroupsScene(),
                  getTotalAlertGroupsByStateScene(),
                  getNewAlertGroupsForSelectedPeriodScene(),
                  getMTTRScene(),
                  getMTTRChangedForPeriodStatScene(),
                ],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [getNewAlertGroupsDuringTimePeriodScene()],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [getMTTRChangedForPeriodTimeseriesScene()],
              }),
            ],
          }),
        }),
        new NestedScene({
          title: 'Integrations data',
          canCollapse: true,
          isCollapsed: false,
          body: new SceneFlexLayout({
            height: 400,
            children: [getAlertGroupsByIntegrationScene(), getMTTRByIntegrationScene()],
          }),
        }),
        new NestedScene({
          title: 'Notified alert groups by Users (based on all Integrations)',
          canCollapse: true,
          isCollapsed: false,
          body: new SceneFlexLayout({
            direction: 'column',
            children: [
              new SceneFlexLayout({
                height: 400,
                children: [getNewAlertGroupsNotificationsDuringTimePeriodScene()],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [
                  getNewAlertGroupsNotificationsInTotalScene(),
                  getNewAlertGroupsNotificationsForPeriodTableScene(),
                ],
              }),
            ],
          }),
        }),
        new NestedScene({
          title: 'Teams data',
          canCollapse: true,
          isCollapsed: false,
          body: new SceneFlexLayout({
            direction: 'column',
            children: [
              new SceneFlexLayout({
                height: 400,
                children: [getAlertGroupsByTeamScene(), getMTTRByTeamScene()],
              }),
            ],
          }),
        }),
      ],
    }),
  });

export default Insights;
