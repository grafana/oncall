import React, { useEffect, useState } from 'react';

import { Alert } from '@grafana/ui';
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
import { Route, Switch, useLocation } from 'react-router-dom';
import { AppRootProps } from 'types';

import Unauthorized from 'components/Unauthorized';
import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import { getMatchedPage, getRoutesForPage, pages } from 'pages';
import NoMatch from 'pages/NoMatch';
import EscalationChains from 'pages/escalation-chains/EscalationChains';
import Incident from 'pages/incident/Incident';
import Incidents from 'pages/incidents/Incidents';
import Integrations from 'pages/integrations/Integrations';
import Maintenance from 'pages/maintenance/Maintenance';
import OrganizationLogPage from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import Schedule from 'pages/schedule/Schedule';
import Schedules from 'pages/schedules/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import Test from 'pages/test/Test';
import Users from 'pages/users/Users';
import 'interceptors';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { isUserActionAllowed } from 'utils/authorization';

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

export const PLUGIN_ROOT = '/a/grafana-oncall-app';

export const GrafanaPluginRootPage = (props: AppRootProps) => {
  return (
    <Provider store={rootStore}>
      <PluginSetup InitializedComponent={Root} {...props} />
    </Provider>
  );
};

export const Root = observer((props: AppRootProps) => {
  const [didFinishLoading, setDidFinishLoading] = useState(false);

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

  if (!didFinishLoading) {
    return null;
  }

  const location = useLocation();

  const page = getMatchedPage(location.pathname);

  const pagePermissionAction = pages[page]?.action;
  const userHasAccess = pagePermissionAction ? isUserActionAllowed(pagePermissionAction) : true;

  const query = getQueryParams();

  return (
    <DefaultPageLayout {...props}>
      <Alert severity="warning" title="Connectivity Warning" />
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
          <Switch>
            <Route path={getRoutesForPage('incidents')} exact>
              <Incidents query={query} />
            </Route>
            <Route path={getRoutesForPage('incident')} exact>
              <Incident query={query} />
            </Route>
            <Route path={getRoutesForPage('users')} exact>
              <Users query={query} />
            </Route>
            <Route path={getRoutesForPage('integrations')} exact>
              <Integrations query={query} />
            </Route>
            <Route path={getRoutesForPage('escalations')} exact>
              <EscalationChains />
            </Route>
            <Route path={getRoutesForPage('schedules')} exact>
              <Schedules />
            </Route>
            <Route path={getRoutesForPage('schedule')} exact>
              <Schedule />
            </Route>
            <Route path={getRoutesForPage('outgoing_webhooks')} exact>
              <OutgoingWebhooks />
            </Route>
            <Route path={getRoutesForPage('maintenance')} exact>
              <Maintenance query={query} />
            </Route>
            <Route path={getRoutesForPage('settings')} exact>
              <SettingsPage />
            </Route>
            <Route path={getRoutesForPage('organization-logs')} exact>
              <OrganizationLogPage />
            </Route>
            <Route path={getRoutesForPage('test')} exact>
              <Test />
            </Route>
            <Route path="*">
              <NoMatch />
            </Route>
          </Switch>
        ) : (
          <Unauthorized requiredUserAction={pagePermissionAction} />
        )}
      </div>
    </DefaultPageLayout>
  );
});
