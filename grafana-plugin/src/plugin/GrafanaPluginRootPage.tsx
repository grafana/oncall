import React, { useEffect } from 'react';

import { ErrorBoundary, LoadingPlaceholder } from '@grafana/ui';
import classnames from 'classnames';
import { observer, Provider } from 'mobx-react';
import { Header } from 'navbar/Header/Header';
import { LegacyNavTabsBar } from 'navbar/LegacyNavTabsBar';
import { Redirect, Route, Switch, useLocation } from 'react-router-dom';
import { AppRootProps } from 'types';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Unauthorized } from 'components/Unauthorized/Unauthorized';
import { DefaultPageLayout } from 'containers/DefaultPageLayout/DefaultPageLayout';
import { NoMatch } from 'pages/NoMatch';
import { EscalationChainsPage } from 'pages/escalation-chains/EscalationChains';
import { IncidentPage } from 'pages/incident/Incident';
import { IncidentsPage } from 'pages/incidents/Incidents';
import { Insights } from 'pages/insights/Insights';
import { IntegrationPage } from 'pages/integration/Integration';
import { IntegrationsPage } from 'pages/integrations/Integrations';
import { OutgoingWebhooksPage } from 'pages/outgoing_webhooks/OutgoingWebhooks';
import { getMatchedPage, getRoutesForPage, pages } from 'pages/pages';
import { SchedulePage } from 'pages/schedule/Schedule';
import { SchedulesPage } from 'pages/schedules/Schedules';
import { SettingsPage } from 'pages/settings/SettingsPage';
import { ChatOpsPage } from 'pages/settings/tabs/ChatOps/ChatOps';
import { CloudPage } from 'pages/settings/tabs/Cloud/CloudPage';
import LiveSettings from 'pages/settings/tabs/LiveSettings/LiveSettingsPage';
import { UsersPage } from 'pages/users/Users';
import { PluginSetup } from 'plugin/PluginSetup/PluginSetup';
import { rootStore } from 'state/rootStore';
import { useStore } from 'state/useStore';
import { isUserActionAllowed } from 'utils/authorization/authorization';
import { DEFAULT_PAGE, getOnCallApiUrl } from 'utils/consts';
import 'assets/style/vars.css';
import 'assets/style/global.css';
import 'assets/style/utils.css';
import { FaroHelper } from 'utils/faro';
import { useOnMount } from 'utils/hooks';

import { getQueryParams, isTopNavbar } from './GrafanaPluginRootPage.helpers';

import grafanaGlobalStyle from '!raw-loader!assets/style/grafanaGlobalStyles.css';

export const GrafanaPluginRootPage = (props: AppRootProps) => {
  useOnMount(() => {
    FaroHelper.initializeFaro(getOnCallApiUrl(props.meta));
  });

  return (
    <ErrorBoundary onError={FaroHelper.pushReactError}>
      {() => (
        <Provider store={rootStore}>
          <PluginSetup InitializedComponent={Root} {...props} />
        </Provider>
      )}
    </ErrorBoundary>
  );
};

export const Root = observer((props: AppRootProps) => {
  const { isBasicDataLoaded, loadBasicData, loadMasterData, pageTitle } = useStore();

  const location = useLocation();

  useEffect(() => {
    loadBasicData();
    // defer loading master data as it's not used in first sec by user in order to prioritize fetching base data
    const timeout = setTimeout(() => {
      loadMasterData();
    }, 1000);

    return () => clearTimeout(timeout);
  }, []);

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

  const page = getMatchedPage(location.pathname);
  const pagePermissionAction = pages[page]?.action;
  const userHasAccess = pagePermissionAction ? isUserActionAllowed(pagePermissionAction) : true;
  const query = getQueryParams();

  const getPageNav = () => {
    return (pages[page] || pages[DEFAULT_PAGE]).getPageNav(pageTitle);
  };

  if (!userHasAccess) {
    return <Unauthorized requiredUserAction={pagePermissionAction} />;
  }

  return (
    <DefaultPageLayout {...props} page={page} pageNav={getPageNav()}>
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
        <RenderConditionally
          shouldRender={userHasAccess}
          backupChildren={<Unauthorized requiredUserAction={pagePermissionAction} />}
        >
          <RenderConditionally
            shouldRender={isBasicDataLoaded}
            backupChildren={<LoadingPlaceholder text="Loading..." />}
          >
            <Switch>
              <Route path={getRoutesForPage('alert-groups')} exact>
                <IncidentsPage query={query} />
              </Route>
              <Route path={getRoutesForPage('alert-group')} exact>
                <IncidentPage query={query} />
              </Route>
              <Route path={getRoutesForPage('users')} exact>
                <UsersPage query={query} />
              </Route>
              <Route path={getRoutesForPage('integrations')} exact>
                <IntegrationsPage query={query} />
              </Route>
              <Route path={getRoutesForPage('integration')} exact>
                <IntegrationPage query={query} />
              </Route>
              <Route path={getRoutesForPage('escalations')} exact>
                <EscalationChainsPage query={query} />
              </Route>
              <Route path={getRoutesForPage('schedules')} exact>
                <SchedulesPage query={query} />
              </Route>
              <Route path={getRoutesForPage('schedule')} exact>
                <SchedulePage query={query} />
              </Route>
              <Route path={getRoutesForPage('outgoing_webhooks')} exact>
                <OutgoingWebhooksPage query={query} />
              </Route>
              <Route path={getRoutesForPage('settings')} exact>
                <SettingsPage />
              </Route>
              <Route path={getRoutesForPage('chat-ops')} exact>
                <ChatOpsPage query={query} />
              </Route>
              <Route path={getRoutesForPage('live-settings')} exact>
                <LiveSettings />
              </Route>
              <Route path={getRoutesForPage('cloud')} exact>
                <CloudPage />
              </Route>
              <Route path={getRoutesForPage('insights')} exact>
                <Insights />
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
              />
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
              />
              <Route path="*">
                <NoMatch />
              </Route>
            </Switch>
          </RenderConditionally>
        </RenderConditionally>
      </div>
    </DefaultPageLayout>
  );
});
