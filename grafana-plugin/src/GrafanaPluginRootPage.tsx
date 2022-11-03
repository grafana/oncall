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

import Unauthorized from 'components/Unauthorized';
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
  const store = useStore();

  useEffect(() => {
    store.setupPlugin(props.meta);
  }, []);

  if (store.appLoading) {
    let text = 'Initializing plugin...';

    if (!store.pluginIsInitialized) {
      text = '🚫 Plugin has not been initialized';
    } else if (!store.correctProvisioningForInstallation) {
      text = '🚫 Plugin could not be initialized due to provisioning error';
    } else if (!store.currentUserHasPermissionForInstallation) {
      text =
        '🚫 An admin (or a user with the "Plugin Maintainer" role granted) must sign on to setup OnCall before it can be used';
    } else if (!store.signupAllowedForPlugin) {
      text = '🚫 OnCall has temporarily disabled signup of new users. Please try again later.';
    } else if (store.initializationError) {
      text = `🚫 Error during initialization: ${store.initializationError}`;
    } else if (store.isUserAnonymous) {
      text = '😞 Unfortunately Grafana OnCall is available for authorized users only, please sign in to proceed.';
    } else if (store.retrySync) {
      text = `🚫 OnCall took too many tries to synchronize... Are background workers up and running?`;
    }

    return (
      <div className="spin">
        <img alt="Grafana OnCall Logo" src={logo} />
        <div className="spin-text">{text}</div>
        {!store.pluginIsInitialized ||
        !store.correctProvisioningForInstallation ||
        store.initializationError ||
        store.retrySync ? (
          <div className="configure-plugin">
            <HorizontalGroup>
              <Button variant="primary" onClick={() => store.setupPlugin(props.meta)} size="sm">
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

  // Required to support grafana instances that use a custom `root_url`.
  const pathWithoutLeadingSlash = path.replace(/^\//, '');

  const store = useStore();
  const { backendLicense } = store;

  useEffect(() => {
    store.updateBasicData();
  }, []);

  useEffect(() => {
    let link = document.createElement('link');
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
    // TODO: do we really need useMemo here??
    useMemo(
      () => ({
        page,
        pages,
        path: pathWithoutLeadingSlash,
        meta,
        store,
        enableLiveSettings: store.hasFeature(AppFeature.LiveSettings),
        enableCloudPage: store.hasFeature(AppFeature.CloudConnection),
        enableNewSchedulesPage: store.hasFeature(AppFeature.WebSchedules),
        backendLicense,
      }),
      [meta, pathWithoutLeadingSlash, page, store, store.features, backendLicense]
    )
  );

  useEffect(() => {
    /* @ts-ignore */
    onNavChanged(navModel);
  }, [navModel, onNavChanged]);

  const { action: pagePermissionAction, component: PageComponent } = pages.find(({ id }) => id === page) || pages[0];
  const userHasAccess = pagePermissionAction ? store.isUserActionAllowed(pagePermissionAction) : true;

  return (
    <DefaultPageLayout {...props}>
      <GrafanaTeamSelect currentPage={page} />
      {userHasAccess ? (
        <PageComponent {...props} path={pathWithoutLeadingSlash} />
      ) : (
        <Unauthorized requiredUserAction={pagePermissionAction} />
      )}
    </DefaultPageLayout>
  );
});
