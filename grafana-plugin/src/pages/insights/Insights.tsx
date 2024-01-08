import React, { useState } from 'react';

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
  SceneApp,
  SceneAppPage,
  useSceneApp,
} from '@grafana/scenes';
import { Alert } from '@grafana/ui';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { useStore } from 'state/useStore';
import { DOCS_ROOT } from 'utils/consts';

import styles from './Insights.module.scss';
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
  const { isOpenSource, insightsDatasource } = useStore();

  const datasource = { uid: isOpenSource ? '$datasource' : insightsDatasource };
  const appScene = useSceneApp(() => getAppScene({ isOpenSource, datasource }));

  return (
    <div className={styles.insights}>
      <InsightsInfoAlert />
      <appScene.Component model={appScene} />
    </div>
  );
});

const InsightsInfoAlert = observer(() => {
  const { isOpenSource } = useStore();
  const [alertVisible, setAlertVisible] = useState(true);

  const docsLink = (
    <a
      href={`${DOCS_ROOT}/insights-and-metrics/${isOpenSource ? '#for-open-source-customers' : ''}`}
      target="_blank"
      rel="noreferrer"
    >
      <Text type="link">documentation</Text>
    </a>
  );

  const content = isOpenSource ? (
    <>
      In order to see insights you need to set up Prometheus, add it to your Grafana instance as a data source, set
      FEATURE_PROMETHEUS_EXPORTER_ENABLED environment variable to true and then select your Data source in the dropdown
      below.
      <br />
      <br />
      <>You can find out more in our {docsLink}.</>
    </>
  ) : (
    <>Find out more about OnCall Insights and Metrics in our {docsLink}.</>
  );

  return alertVisible ? (
    <Alert onRemove={() => setAlertVisible(false)} severity="info" title="">
      {content}
    </Alert>
  ) : null;
});

const getAppScene = (config: InsightsConfig) =>
  new SceneApp({
    pages: [
      new SceneAppPage({
        title: 'OnCall Insights',
        url: '/a/grafana-oncall-app/insights',
        getScene: () => getRootScene(config),
      }),
    ],
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
