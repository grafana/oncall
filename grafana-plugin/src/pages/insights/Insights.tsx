import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { css } from '@emotion/css';
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
import { Alert, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { DOCS_ROOT, StackSize, PLUGIN_ROOT, IS_CURRENT_ENV_OSS } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { Tutorial } from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { useStore } from 'state/useStore';

import { useAlertCreationChecker } from './Insights.hooks';
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
    insightsDatasource,
    organizationStore: { currentOrganization },
  } = useStore();
  const [datasource, setDatasource] = useState<string>();
  const { isAnyAlertCreatedMoreThan20SecsAgo, isFirstAlertCheckDone } = useAlertCreationChecker();

  const config = useMemo(
    () => ({
      isOpenSource: IS_CURRENT_ENV_OSS,
      datasource: { uid: IS_CURRENT_ENV_OSS ? '$datasource' : insightsDatasource },
      stack: currentOrganization?.stack_slug,
    }),
    [currentOrganization?.stack_slug]
  );

  const variables = useMemo(() => getVariables(config), [config]);

  const getAppScene = useCallback(() => getRootScene(config, variables), [config, variables]);

  const appScene = useSceneApp(getAppScene);

  const styles = useStyles2(getStyles);

  useEffect(() => {
    if (!isAnyAlertCreatedMoreThan20SecsAgo) {
      return undefined;
    }
    const dataSourceListener =
      IS_CURRENT_ENV_OSS &&
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
          {IS_CURRENT_ENV_OSS && !datasource && <NoDatasourceWarning />}
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
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.spaceTop}>
      <Tutorial
        step={TutorialStep.Integrations}
        title={
          <Stack direction="column" alignItems="center" gap={StackSize.lg}>
            <Text type="secondary">
              Your OnCall stack doesn’t have any alerts to visualise insights.
              <br />
              Make sure that you setup OnCall configuration to start monitoring.
            </Text>
          </Stack>
        }
      />
    </div>
  );
};

const NoDatasourceWarning = () => {
  const styles = useStyles2(getStyles);
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

const getStyles = () => {
  return {
    // Required to remove inner page padding since grafana-scenes doesn't support its style modification
    insights: css`
      div[class*='page-inner'] {
        padding-left: 0;
        padding-right: 0;
        border: none;
        margin: 0;
      }
    `,

    spaceTop: css`
      margin-top: 16px;
    `,

    alertBox: css`
      margin-top: 32px;
    `,
  };
};
