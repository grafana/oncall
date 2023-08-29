import React, { useEffect, useState } from 'react';

import { LoadingPlaceholder } from '@grafana/ui';
import classnames from 'classnames';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import isBetween from 'dayjs/plugin/isBetween';
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
import { Redirect, Route, Switch, useLocation } from 'react-router-dom';
import { AppRootProps } from 'types';

import Unauthorized from 'components/Unauthorized';
import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import { getMatchedPage, getRoutesForPage, pages } from 'pages';
import NoMatch from 'pages/NoMatch';
import EscalationChains from 'pages/escalation-chains/EscalationChains';
import Incident from 'pages/incident/Incident';
import Incidents from 'pages/incidents/Incidents';
import Integration from 'pages/integration/Integration';
import Integrations from 'pages/integrations/Integrations';
import Maintenance from 'pages/maintenance/Maintenance';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import Schedule from 'pages/schedule/Schedule';
import Schedules from 'pages/schedules/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import ChatOps from 'pages/settings/tabs/ChatOps/ChatOps';
import CloudPage from 'pages/settings/tabs/Cloud/CloudPage';
import LiveSettings from 'pages/settings/tabs/LiveSettings/LiveSettingsPage';
import Users from 'pages/users/Users';
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
dayjs.extend(isBetween);
dayjs.extend(customParseFormat);

import 'assets/style/vars.css';
import 'assets/style/global.css';
import 'assets/style/utils.css';
import 'assets/style/responsive.css';

import { getQueryParams, isTopNavbar } from './GrafanaPluginRootPage.helpers';
import PluginSetup from './PluginSetup';

import grafanaGlobalStyle from '!raw-loader!assets/style/grafanaGlobalStyles.css';

export const GrafanaPluginRootPage = (props: AppRootProps) => {
  return (
    <Provider store={rootStore}>
      <PluginSetup InitializedComponent={Root} {...props} />
    </Provider>
  );
};

export const Root = observer((props: AppRootProps) => {
  const store = useStore();

  const [basicDataLoaded, setBasicDataLoaded] = useState(false);

  useEffect(() => {
    updateBasicData();
  }, []);

  const location = useLocation();

  useEffect(() => {
    let link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';

    // create a style element
    const styleEl = document.createElement('style');
    const head = document.head || document.getElementsByTagName('head')[0];
    styleEl.appendChild(document.createTextNode(grafanaGlobalStyle));

    // append grafana overriding styles to head
    head.appendChild(styleEl);

    document.head.appendChild(link);

    return () => {
      head.removeChild(styleEl); // remove on unmount
    };
  }, []);

  const updateBasicData = async () => {
    await store.updateBasicData();
    setBasicDataLoaded(true);
  };

  const page = getMatchedPage(location.pathname);
  const pagePermissionAction = pages[page]?.action;
  const userHasAccess = pagePermissionAction ? isUserActionAllowed(pagePermissionAction) : true;
  const query = getQueryParams();

  return (
    <DefaultPageLayout {...props} page={page}>
      {!isTopNavbar() && (
        <>
          <Header />
          <LegacyNavTabsBar currentPage={page} />
        </>
      )}

      <div
        className={classnames('u-position-relative', 'u-flex-grow-1', {
          'u-overflow-x-auto': !isTopNavbar(),
          'page-body': !isTopNavbar(),
        })}
      >
        {userHasAccess ? (
          // Otherwise we'll run into concurrency issues
          !basicDataLoaded ? (
            <LoadingPlaceholder text="Loading..." />
          ) : (
            <Switch>
              <Route path={getRoutesForPage('alert-groups')} exact>
                <Incidents query={query} />
              </Route>
              <Route path={getRoutesForPage('alert-group')} exact>
                <Incident query={query} />
              </Route>
              <Route path={getRoutesForPage('users')} exact>
                <Users query={query} />
              </Route>
              <Route path={getRoutesForPage('integrations')} exact>
                <Integrations query={query} />
              </Route>
              <Route path={getRoutesForPage('integration')} exact>
                <Integration query={query} />
              </Route>
              <Route path={getRoutesForPage('escalations')} exact>
                <EscalationChains query={query} />
              </Route>
              <Route path={getRoutesForPage('schedules')} exact>
                <Schedules query={query} />
              </Route>
              <Route path={getRoutesForPage('schedule')} exact>
                <Schedule query={query} />
              </Route>
              <Route path={getRoutesForPage('outgoing_webhooks')} exact>
                <OutgoingWebhooks query={query} />
              </Route>
              <Route path={getRoutesForPage('maintenance')} exact>
                <Maintenance />
              </Route>
              <Route path={getRoutesForPage('settings')} exact>
                <SettingsPage />
              </Route>
              <Route path={getRoutesForPage('chat-ops')} exact>
                <ChatOps query={query} />
              </Route>
              <Route path={getRoutesForPage('live-settings')} exact>
                <LiveSettings />
              </Route>
              <Route path={getRoutesForPage('cloud')} exact>
                <CloudPage />
              </Route>

              {/* Backwards compatibility redirect routes */}
              <Route
                path={getRoutesForPage('incident')}
                exact
                render={({ location }) => (
                  <Redirect
                    to={{
                      ...location,
                      pathname: location.pathname.replace(/incident/, 'alert-group'),
                    }}
                  ></Redirect>
                )}
              ></Route>
              <Route
                path={getRoutesForPage('incidents')}
                exact
                render={({ location }) => (
                  <Redirect
                    to={{
                      ...location,
                      pathname: location.pathname.replace(/incidents/, 'alert-groups'),
                    }}
                  ></Redirect>
                )}
              ></Route>

              <Route path="*">
                <NoMatch />
              </Route>
            </Switch>
          )
        ) : (
          <Unauthorized requiredUserAction={pagePermissionAction} />
        )}
      </div>
    </DefaultPageLayout>
  );
});
