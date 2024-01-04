import React, { useMemo, useState } from 'react';

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
import { getDataSource } from './Insights.helpers';
import { Alert } from '@grafana/ui';
import Text from 'components/Text/Text';
import { DOCS_ROOT } from 'utils/consts';

const Insights = observer(() => {
  const { isOpenSource } = useStore();
  const [alertVisible, setAlertVisible] = useState(true);

  const rootScene = useMemo(
    () => getRootScene({ isOpenSource, datasource: getDataSource(isOpenSource) }),
    [isOpenSource]
  );

  return (
    <>
      {isOpenSource && alertVisible && (
        <Alert onRemove={() => setAlertVisible(false)} severity="info" title="">
          {
            <>
              In order to see insights you need to set up Prometheus, add it to your Grafana instance as a data source
              and select in Data source dropdown.{' '}
              <>
                You can find out more in
                <a
                  href={`${DOCS_ROOT}/insights-and-metrics/#for-open-source-customers`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Text type="link"> documentation</Text>
                </a>
                .
              </>
            </>
          }
        </Alert>
      )}
      <rootScene.Component model={rootScene} />
    </>
  );
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
                  getTotalAlertGroupsScene(config),
                  getTotalAlertGroupsByStateScene(config),
                  getNewAlertGroupsForSelectedPeriodScene(config),
                  getMTTRScene(config),
                  getMTTRChangedForPeriodStatScene(config),
                ],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [getNewAlertGroupsDuringTimePeriodScene(config)],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [getMTTRChangedForPeriodTimeseriesScene(config)],
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
            children: [getAlertGroupsByIntegrationScene(config), getMTTRByIntegrationScene(config)],
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
                children: [getNewAlertGroupsNotificationsDuringTimePeriodScene(config)],
              }),
              new SceneFlexLayout({
                height: 400,
                children: [
                  getNewAlertGroupsNotificationsInTotalScene(config),
                  getNewAlertGroupsNotificationsForPeriodTableScene(config),
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
                children: [getAlertGroupsByTeamScene(config), getMTTRByTeamScene(config)],
              }),
            ],
          }),
        }),
      ],
    }),
  });

export default Insights;
