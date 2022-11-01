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
import { rootStore } from 'state';
import { useStore } from 'state/useStore';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(weekday);
dayjs.extend(localeData);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);
dayjs.extend(isoWeek);

import './style/vars.css';
import './style/global.css';

import { routes } from 'components/PluginLink/routes';
import { useQueryParams, useQueryPath } from 'utils/hooks';
import { pages } from 'pages/routes';

import { locationService } from '@grafana/runtime';

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
    } else if (!store.correctRoleForInstallation) {
      text = '🚫 Admin must sign on to setup OnCall before a Viewer can use it';
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
  const queryParams = useQueryParams();
  const page = queryParams.get('page');
  const path = useQueryPath();

  // Required to support grafana instances that use a custom `root_url`.
  const pathWithoutLeadingSlash = path.replace(/^\//, '');

  const store = useStore();

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

  const Page = useMemo(() => {
    return getPageMatchingComponent(page);
  }, [page]);

  return (
    <DefaultPageLayout {...props}>
      <GrafanaTeamSelect currentPage={page} />
      <Page {...props} path={pathWithoutLeadingSlash} />
    </DefaultPageLayout>
  );
});

function getPageMatchingComponent(pageId: string): (props?: any) => JSX.Element {
  let matchingPage = routes[pageId];
  if (!matchingPage) {
    const defaultPageId = Object.keys(pages)[0];
    matchingPage = routes[defaultPageId];
    locationService.replace(pages[defaultPageId].path);
  }

  return matchingPage.component;
}
