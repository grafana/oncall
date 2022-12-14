import React, { useEffect, useMemo, useState } from 'react';

import { initializeFaro, getWebInstrumentations } from '@grafana/faro-web-sdk';
import { TracingInstrumentation, getDefaultOTELInstrumentations } from '@grafana/faro-web-tracing';
import { locationService } from '@grafana/runtime';
import classnames from 'classnames';
import dayjs from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import isoWeek from 'dayjs/plugin/isoWeek';
import localeData from 'dayjs/plugin/localeData';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import weekday from 'dayjs/plugin/weekday';
import { observer, Provider } from 'mobx-react';
import Header from 'navbar/Header/Header';
import LegacyNavTabsBar from 'navbar/LegacyNavTabsBar';

import plugin from '../../package.json'; // eslint-disable-line
import { AppRootProps } from 'types';

import Unauthorized from 'components/Unauthorized';
import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import 'interceptors';
import { pages } from 'pages';
import { routes } from 'pages/routes';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { isUserActionAllowed } from 'utils/authorization';
import { useQueryParams, useQueryPath } from 'utils/hooks';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(weekday);
dayjs.extend(localeData);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);
dayjs.extend(isoWeek);

import 'style/vars.css';
import 'style/global.css';
import 'style/utils.css';

import { getQueryParams, isTopNavbar } from './GrafanaPluginRootPage.helpers';
import PluginSetup from './PluginSetup';

export const GrafanaPluginRootPage = (props: AppRootProps) => (
  <Provider store={rootStore}>
    <PluginSetup InitializedComponent={Root} {...props} />
  </Provider>
);

export const Root = observer((props: AppRootProps) => {
  const [didFinishLoading, setDidFinishLoading] = useState(false);
  const queryParams = useQueryParams();
  const page = queryParams.get('page');
  const path = useQueryPath();

  // Required to support grafana instances that use a custom `root_url`.
  const pathWithoutLeadingSlash = path.replace(/^\//, '');

  const store = useStore();

  useEffect(() => {
    updateBasicData();
  }, []);

  useEffect(() => {
    let link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';
    link.href = '/public/plugins/grafana-oncall-app/img/grafanaGlobalStyles.css';

    document.head.appendChild(link);

    initFaro();

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  const updateBasicData = async () => {
    await store.updateBasicData();
    setDidFinishLoading(true);
  };

  const Page = useMemo(() => getPageMatchingComponent(page), [page]);

  if (!didFinishLoading) {
    return null;
  }

  const { action: pagePermissionAction } = pages[page];
  const userHasAccess = pagePermissionAction ? isUserActionAllowed(pagePermissionAction) : true;

  return (
    <DefaultPageLayout {...props}>
      {!isTopNavbar() && (
        <>
          <Header page={page} backendLicense={store.backendLicense} />
          <nav className="page-container">
            <LegacyNavTabsBar currentPage={page} />
          </nav>
        </>
      )}

      <div
        className={classnames(
          { 'page-container': !isTopNavbar() },
          { 'page-body': !isTopNavbar() },
          'u-position-relative'
        )}
      >
        {userHasAccess ? (
          <Page {...props} query={...getQueryParams()} path={pathWithoutLeadingSlash} store={store} />
        ) : (
          <Unauthorized requiredUserAction={pagePermissionAction} />
        )}
      </div>
    </DefaultPageLayout>
  );
});

function initFaro() {
  const faro = initializeFaro({
    url: `http://localhost:12345/collect`,
    apiKey: 'secret',
    instrumentations: [
      ...getWebInstrumentations({
        captureConsole: true,
      }),
      new TracingInstrumentation({
        instrumentations: [...getDefaultOTELInstrumentations([/^((?!\/{0,1}a\/grafana\-oncall\-app\\).)*$/])],
      }),
    ],
    session: (window as any).__PRELOADED_STATE__?.faro?.session,
    app: {
      name: plugin?.name || 'Grafana OnCall',
      version: plugin?.version || '1.0.0',
      // environment: 'dev', // TODO: sort this out
    },
  });

  faro.api.pushLog(['Faro was initialized for Grafana On Call']);
}

function getPageMatchingComponent(pageId: string): (props?: any) => JSX.Element {
  let matchingPage = routes[pageId];
  if (!matchingPage) {
    const defaultPageId = pages['incidents'].id;
    matchingPage = routes[defaultPageId];
    locationService.replace(pages[defaultPageId].path);
  }

  return matchingPage.component;
}
