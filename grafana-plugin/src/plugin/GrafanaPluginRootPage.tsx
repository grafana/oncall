import React, { useEffect, useMemo, useState } from 'react';

import { locationService } from '@grafana/runtime';
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
import { AppRootProps } from 'types';

import Unauthorized from 'components/Unauthorized';
import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import 'interceptors';
import { pages } from 'pages';
import { routes } from 'pages/routes';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { isUserActionAllowed } from 'utils/authorization';
import { DEFAULT_PAGE } from 'utils/consts';
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
  const page = queryParams.get('page') || DEFAULT_PAGE;
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
          <LegacyNavTabsBar currentPage={page} />
        </>
      )}

      <div className="page-body u-position-relative u-overflow-x-auto">
        {userHasAccess ? (
          <Page {...props} query={...getQueryParams()} path={pathWithoutLeadingSlash} store={store} />
        ) : (
          <Unauthorized requiredUserAction={pagePermissionAction} />
        )}
      </div>
    </DefaultPageLayout>
  );
});

function getPageMatchingComponent(pageId: string): (props?: any) => JSX.Element {
  let matchingPage = routes[pageId];
  if (!matchingPage) {
    const defaultPageId = pages['incidents'].id;
    matchingPage = routes[defaultPageId];
    locationService.replace(pages[defaultPageId].path);
  }

  return matchingPage.component;
}
