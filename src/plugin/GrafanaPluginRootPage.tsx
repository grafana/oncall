import React, { useEffect } from 'react';

import { css, cx } from '@emotion/css';
import { ErrorBoundary, LoadingPlaceholder } from '@grafana/ui';
import { AppRootProps } from 'app-types';
import { isUserActionAllowed } from 'helpers/authorization/authorization';
import { DEFAULT_PAGE, getOnCallApiUrl } from 'helpers/consts';
import { FaroHelper } from 'helpers/faro';
import { useOnMount } from 'helpers/hooks';
import { observer, Provider } from 'mobx-react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom-v5-compat';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Unauthorized } from 'components/Unauthorized/Unauthorized';
import { DefaultPageLayout } from 'containers/DefaultPageLayout/DefaultPageLayout';
import { PluginInitializer } from 'containers/PluginInitializer/PluginInitializer';
import { NoMatch } from 'pages/NoMatch';
import { EscalationChainsPage } from 'pages/escalation-chains/EscalationChains';
import { IncidentPage } from 'pages/incident/Incident';
import { IncidentsPage } from 'pages/incidents/Incidents';
import { Insights } from 'pages/insights/Insights';
import { IntegrationPage } from 'pages/integration/Integration';
import { IntegrationsPage } from 'pages/integrations/Integrations';
import { OutgoingWebhooksPage } from 'pages/outgoing_webhooks/OutgoingWebhooks';
import { getMatchedPage, pages } from 'pages/pages';
import { SchedulePage } from 'pages/schedule/Schedule';
import { SchedulesPage } from 'pages/schedules/Schedules';
import { SettingsPage } from 'pages/settings/SettingsPage';
import { ChatOpsPage } from 'pages/settings/tabs/ChatOps/ChatOps';
import { CloudPage } from 'pages/settings/tabs/Cloud/CloudPage';
import { LiveSettings } from 'pages/settings/tabs/LiveSettings/LiveSettingsPage';
import { UsersPage } from 'pages/users/Users';
import { rootStore } from 'state/rootStore';
import { useStore } from 'state/useStore';

import { getQueryParams } from './GrafanaPluginRootPage.helpers';

import globalStyles from '!raw-loader!assets/style/global.css';
import grafanaGlobalStyle from '!raw-loader!assets/style/grafanaGlobalStyles.css';

export const GrafanaPluginRootPage = observer((props: AppRootProps) => {
  useOnMount(() => {
    FaroHelper.initializeFaro(getOnCallApiUrl(props.meta));
  });

  return (
    <ErrorBoundary onError={FaroHelper.pushReactError}>
      {() => (
        <PluginInitializer>
          <Provider store={rootStore}>
            <Root {...props} />
          </Provider>
        </PluginInitializer>
      )}
    </ErrorBoundary>
  );
});

export const Root = observer((props: AppRootProps) => {
  const { isBasicDataLoaded, loadBasicData, loadMasterData, pageTitle, setupInsightsDatasource, loadRecaptcha } =
    useStore();

  const location = useLocation();

  useEffect(() => {
    setupInsightsDatasource(props.meta);
    loadRecaptcha();
    loadBasicData();
    // defer loading master data as it's not used in first sec by user in order to prioritize fetching base data
    const timeout = setTimeout(() => {
      loadMasterData();
    }, 1000);

    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line deprecation/deprecation
    let link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';

    // eslint-disable-next-line deprecation/deprecation
    const styleEl = document.createElement('style');
    const head = document.head || document.getElementsByTagName('head')[0];
    styleEl.appendChild(document.createTextNode(grafanaGlobalStyle));
    styleEl.appendChild(document.createTextNode(globalStyles));

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
      <div
        className={cx(
          css`
            position: relative;
            flex-grow: 1;
          `,
        )}
      >
        <RenderConditionally
          shouldRender={userHasAccess}
          backupChildren={<Unauthorized requiredUserAction={pagePermissionAction} />}
        >
          <RenderConditionally
            shouldRender={isBasicDataLoaded}
            backupChildren={<LoadingPlaceholder text="Loading..." />}
            render={() => (
              <Routes>
                <Route path="alert-groups">
                  <Route path=":id" element={<IncidentPage query={query} />} />
                  <Route index element={<IncidentsPage query={query} />} />
                </Route>

                <Route path="users">
                  <Route path=":id" element={<UsersPage query={query} />} />
                  <Route index element={<UsersPage query={query} />} />
                </Route>

                <Route path="integrations">
                  <Route path=":id" element={<IntegrationPage query={query} />} />
                  <Route index element={<IntegrationsPage query={query} />} />
                </Route>

                <Route path="escalations">
                  <Route path=":id" element={<EscalationChainsPage query={query} />} />
                  <Route index element={<EscalationChainsPage query={query} />} />
                </Route>

                <Route path="schedules">
                  <Route path=":id" element={<SchedulePage query={query} />} />
                  <Route index element={<SchedulesPage query={query} />} />
                </Route>

                <Route path="outgoing_webhooks">
                  <Route path=":action/:id" element={<OutgoingWebhooksPage query={query} />} />
                  <Route path=":id" element={<OutgoingWebhooksPage query={query} />} />
                  <Route index element={<OutgoingWebhooksPage query={query} />} />
                </Route>

                <Route path="settings" element={<SettingsPage />} />
                <Route path="chat-ops" element={<ChatOpsPage query={query} />} />
                <Route path="live-settings" element={<LiveSettings />} />
                <Route path="cloud" element={<CloudPage />} />
                <Route path="insights" element={<Insights />} />

                <Route path="incident" element={<Navigate to="alert-group" replace />} />
                <Route path="incidents" element={<Navigate to="alert-groups" replace />} />

                <Route path="*" element={<NoMatch />} />
              </Routes>
            )}
          />
        </RenderConditionally>
      </div>
    </DefaultPageLayout>
  );
});
