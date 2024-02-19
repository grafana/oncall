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
import { Alert, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { Tutorial } from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { useStore } from 'state/useStore';
import { DOCS_ROOT, PLUGIN_ROOT } from 'utils/consts';

import { useAlertCreationChecker } from './Insights.hooks';
import styles from './Insights.module.scss';
import { InsightsConfig } from './Insights.types';
import { getAlertGroupsByIntegrationScene } from './scenes/AlertGroupsByIntegration';
import { getAlertGroupsByTeamScene } from './scenes/AlertGroupsByTeam';
import { getMTTRAverage } from './scenes/MTTRAverageStat';
import { getMTTRByIntegrationScene } from './scenes/MTTRByIntegration';
import { getMTTRByTeamScene } from './scenes/MTTRByTeam';
import { getMTTRChangedTimeseriesScene } from './scenes/MTTRChangedTimeseries';
import { getNewAlertGroupsScene } from './scenes/NewAlertGroups';
import { getNewAlertGroupsNotificationsTableScene } from './scenes/NewAlertGroupsNotificationsTable';
import { getNewAlertGroupsNotificationsTimeseriesScene } from './scenes/NewAlertGroupsNotificationsTimeseries';
import { getNewAlertGroupsTimeseriesScene } from './scenes/NewAlertGroupsTimeseries';
import getVariables from './variables';

export const Insights = observer(() => {
  const {
    isOpenSource,
    insightsDatasource,
    organizationStore: { currentOrganization },
  } = useStore();
  const [datasource, setDatasource] = useState<string>();
  const { isAnyAlertCreatedMoreThan20SecsAgo, isFirstAlertCheckDone } = useAlertCreationChecker();

  const config = useMemo(
    () => ({
      isOpenSource,
      datasource: { uid: isOpenSource ? '$datasource' : insightsDatasource },
      stack: currentOrganization?.stack_slug,
    }),
    [isOpenSource, currentOrganization?.stack_slug]
  );

  const variables = useMemo(() => getVariables(config), [config]);

  const getAppScene = useCallback(() => getRootScene(config, variables), [config, variables]);

  const appScene = useSceneApp(getAppScene);

  useEffect(() => {
    if (!isAnyAlertCreatedMoreThan20SecsAgo) {
      return undefined;
    }
    const dataSourceListener =
      isOpenSource &&
      variables.datasource.subscribeToState(({ text }) => {
        setDatasource(`${text}`);
      });
    return () => {
      dataSourceListener?.unsubscribe?.();
    };
  }, [isAnyAlertCreatedMoreThan20SecsAgo]);

  if (!isFirstAlertCheckDone) {
    return <LoadingPlaceholder text="Loading..." />;
  }
  return (
    <div className={styles.insights}>
      <InsightsGeneralInfo />
      {isAnyAlertCreatedMoreThan20SecsAgo ? (
        <>
          {isOpenSource && !datasource && <NoDatasourceWarning />}
          <appScene.Component model={appScene} />
        </>
      ) : (
        <NoAlertCreatedTutorial />
      )}
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

const NoAlertCreatedTutorial = () => {
  return (
    <div className={styles.spaceTop}>
      <Tutorial
        step={TutorialStep.Integrations}
        title={
          <VerticalGroup align="center" spacing="lg">
            <Text type="secondary">
              Your OnCall stack doesn’t have any alerts to visualise insights.
              <br />
              Make sure that you setup OnCall configuration to start monitoring.
            </Text>
          </VerticalGroup>
        }
      />
    </div>
  );
};

const NoDatasourceWarning = () => {
  const [alertVisible, setAlertVisible] = useState(true);
  const docsLink = (
    <a href={`${DOCS_ROOT}/insights-and-metrics`} target="_blank" rel="noreferrer">
      <Text type="link">documentation</Text>
    </a>
  );

  return alertVisible ? (
    <div className={styles.alertBox}>
      <Alert onRemove={() => setAlertVisible(false)} severity="warning" title="">
        Insights data has missing Prometheus configuration. Open OnCall {docsLink} to see how to setup it.
      </Alert>
    </div>
  ) : null;
};

const getRootScene = (config: InsightsConfig, variables: ReturnType<typeof getVariables>) =>
  new SceneApp({
    pages: [
      new SceneAppPage({
        title: 'OnCall Insights',
        url: `${PLUGIN_ROOT}/insights`,
        getScene: () =>
          new EmbeddedScene({
            $timeRange: new SceneTimeRange({ from: 'now-24h', to: 'now' }),
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
                        height: 300,
                        children: [getNewAlertGroupsScene(config), getMTTRAverage(config)],
                      }),
                      new SceneFlexLayout({
                        height: 300,
                        children: [getNewAlertGroupsTimeseriesScene(config), getMTTRChangedTimeseriesScene(config)],
                      }),
                    ],
                  }),
                }),
                new NestedScene({
                  title: 'Integrations data',
                  canCollapse: true,
                  isCollapsed: false,
                  body: new SceneFlexLayout({
                    height: 300,
                    children: [getAlertGroupsByIntegrationScene(config), getMTTRByIntegrationScene(config)],
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
                        height: 300,
                        children: [getAlertGroupsByTeamScene(config), getMTTRByTeamScene(config)],
                      }),
                    ],
                  }),
                }),
                new NestedScene({
                  title: 'Notified alert groups by Users (based on all Teams and Integrations)',
                  canCollapse: true,
                  isCollapsed: false,
                  body: new SceneFlexLayout({
                    direction: 'column',
                    children: [
                      new SceneFlexLayout({
                        height: 300,
                        children: [
                          getNewAlertGroupsNotificationsTimeseriesScene(config),
                          getNewAlertGroupsNotificationsTableScene(config),
                        ],
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
