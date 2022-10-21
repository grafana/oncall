import React, { useEffect, useMemo } from 'react';

import { AppRootProps } from '@grafana/data';
import { Button, HorizontalGroup, LinkButton } from '@grafana/ui';
import dayjs from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import isoWeek from 'dayjs/plugin/isoWeek';
import localeData from 'dayjs/plugin/localeData';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import weekday from 'dayjs/plugin/weekday';
import { observer, Provider } from 'mobx-react';

import 'interceptors';

import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import logo from 'img/logo.svg';
import { pages } from 'pages';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { useNavModel } from 'utils/hooks';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(weekday);
dayjs.extend(localeData);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);
dayjs.extend(isoWeek);

import './style/vars.css';
import './style/index.css';

import { AppFeature } from './state/features';

export const GrafanaPluginRootPage = (props: AppRootProps) => (
  <Provider store={rootStore}>
    <RootWithLoader {...props} />
  </Provider>
);

const RootWithLoader = observer((props: AppRootProps) => {
  const { meta } = props;
  const {
    setupPlugin,
    appLoading,
    pluginIsInitialized,
    correctProvisioningForInstallation,
    correctRoleForInstallation,
    signupAllowedForPlugin,
    initializationError,
    isUserAnonymous,
    retrySync,
  } = useStore();

  useEffect(() => {
    setupPlugin(meta);
  }, []);

  if (appLoading) {
    let text = 'Initializing plugin...';

    if (!pluginIsInitialized) {
      text = '🚫 Plugin has not been initialized';
    } else if (!correctProvisioningForInstallation) {
      text = '🚫 Plugin could not be initialized due to provisioning error';
    } else if (!correctRoleForInstallation) {
      text = '🚫 Admin must sign on to setup OnCall before a Viewer can use it';
    } else if (!signupAllowedForPlugin) {
      text = '🚫 OnCall has temporarily disabled signup of new users. Please try again later.';
    } else if (initializationError) {
      text = `🚫 Error during initialization: ${initializationError}`;
    } else if (isUserAnonymous) {
      text = '😞 Unfortunately Grafana OnCall is available for authorized users only, please sign in to proceed.';
    } else if (retrySync) {
      text = `🚫 OnCall took too many tries to synchronize... Are background workers up and running?`;
    }

    return (
      <div className="spin">
        <img alt="Grafana OnCall Logo" src={logo} />
        <div className="spin-text">{text}</div>
        {!pluginIsInitialized || !correctProvisioningForInstallation || initializationError || retrySync ? (
          <div className="configure-plugin">
            <HorizontalGroup>
              <Button variant="primary" onClick={() => setupPlugin(meta)} size="sm">
                Retry
              </Button>
              <LinkButton href={`/plugins/grafana-oncall-app?page=configuration`} variant="primary" size="sm">
                Configure Plugin
              </LinkButton>
            </HorizontalGroup>
          </div>
        ) : (
          <></>
        )}
      </div>
    );
  }

  return <Root {...props} />;
});

export const Root = observer((props: AppRootProps) => {
  const {
    path,
    onNavChanged,
    query: { page },
    meta,
  } = props;

  const { backendLicense, updateBasicData, hasFeature, features } = useStore();

  // Required to support grafana instances that use a custom `root_url`.
  const pathWithoutLeadingSlash = path.replace(/^\//, '');

  useEffect(() => {
    updateBasicData();
  }, []);

  useEffect(() => {
    const link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';
    link.href = '/public/plugins/grafana-oncall-app/img/grafanaGlobalStyles.css';

    document.head.appendChild(link);

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  // Update the navigation when the page or path changes
  const navModel = useNavModel(
    useMemo(
      () => ({
        page,
        pages,
        path: pathWithoutLeadingSlash,
        meta,
        grafanaUser: window.grafanaBootData.user,
        enableLiveSettings: hasFeature(AppFeature.LiveSettings),
        enableCloudPage: hasFeature(AppFeature.CloudConnection),
        enableNewSchedulesPage: hasFeature(AppFeature.WebSchedules),
        backendLicense,
      }),
      [meta, pathWithoutLeadingSlash, page, features, backendLicense]
    )
  );

  useEffect(() => {
    /* @ts-ignore */
    onNavChanged(navModel);
  }, [navModel, onNavChanged]);

  const Page = pages.find(({ id }) => id === page)?.component || pages[0].component;

  return (
    <DefaultPageLayout {...props}>
      <GrafanaTeamSelect currentPage={page} />
      <Page {...props} path={pathWithoutLeadingSlash} />
    </DefaultPageLayout>
  );
});
