import React, { useCallback, useEffect, useMemo, useState } from 'react';

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

const getDefaultStackValue = (isOpenSource: boolean) =>
  isOpenSource ? 'self_hosted_stack' : location.host.split('.')[0];

const Insights = observer(() => {
  const { isOpenSource, insightsDatasource } = useStore();
  const [showAllStackInfo, setShowAllStackInfo] = useState(false);
  const [datasource, setDatasource] = useState<string>();

  const config = useMemo(
    () => ({
      isOpenSource,
      datasource: { uid: isOpenSource ? '$datasource' : insightsDatasource },
      stack: getDefaultStackValue(isOpenSource),
    }),
    []
  );

  const variables = useMemo(() => getVariables(config), [config]);

  const getAppScene = useCallback(() => getRootScene(config, variables), [config, variables]);

  const appScene = useSceneApp(getAppScene);

  useEffect(() => {
    const stackListener = variables.stack.subscribeToState(({ text }) => {
      setShowAllStackInfo((text as string[]).includes('All'));
    });
    const dataSourceListener =
      isOpenSource &&
      variables.datasource.subscribeToState(({ text }) => {
        setDatasource(`${text}`);
      });
    return () => {
      if (stackListener?.unsubscribe) {
        stackListener.unsubscribe();
      }
      if (dataSourceListener?.unsubscribe) {
        dataSourceListener.unsubscribe();
      }
    };
  }, []);

  return (
    <div className={styles.insights}>
      <InsightsGeneralInfo />
      {showAllStackInfo && <AllStacksSelectedWarning />}
      {isOpenSource && !datasource && <NoDatasourceWarning />}
      <appScene.Component model={appScene} />
    </div>
  );
});

const InsightsGeneralInfo = () => {
  const docsLink = (
    <a href={`${DOCS_ROOT}/insights-and-metrics`} target="_blank" rel="noreferrer">
      <Text type="link">documentation</Text>
    </a>
  );
  return <Text type="secondary">Find out more about OnCall Insights and Metrics in our {docsLink}.</Text>;
};

const AllStacksSelectedWarning = () => {
  const [alertVisible, setAlertVisible] = useState(true);

  return alertVisible ? (
    <Alert onRemove={() => setAlertVisible(false)} severity="warning" title="" className={styles.alertBox}>
      Retrieving insights from multiple stacks has performance impact and loading data might take significantly more
      time. We recommend to select only specific stacks.
    </Alert>
  ) : null;
};

const NoDatasourceWarning = () => {
  const [alertVisible, setAlertVisible] = useState(true);
  const docsLink = (
    <a href={`${DOCS_ROOT}/insights-and-metrics`} target="_blank" rel="noreferrer">
      <Text type="link">documentation</Text>
    </a>
  );

  return alertVisible ? (
    <Alert onRemove={() => setAlertVisible(false)} severity="warning" title="" className={styles.alertBox}>
      Insights data has missing Prometheus configuration. Open OnCall {docsLink} to see how to setup it.
    </Alert>
  ) : null;
};

const getRootScene = (config: InsightsConfig, variables: ReturnType<typeof getVariables>) =>
  new SceneApp({
    pages: [
      new SceneAppPage({
        title: 'OnCall Insights',
        url: '/a/grafana-oncall-app/insights',
        getScene: () =>
          new EmbeddedScene({
            $timeRange: new SceneTimeRange({ from: 'now-7d', to: 'now' }),
            $variables: new SceneVariableSet({
              variables: Object.values(variables),
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
          }),
      }),
    ],
  });

export default Insights;
