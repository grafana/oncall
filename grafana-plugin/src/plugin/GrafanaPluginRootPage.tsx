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
import { getMatchedPage, pages } from 'pages/pages';
import { rootStore } from 'state/rootStore';
import { useStore } from 'state/useStore';

import { getQueryParams } from './GrafanaPluginRootPage.helpers';

import globalStyles from '!raw-loader!assets/style/global.css';
import grafanaGlobalStyle from '!raw-loader!assets/style/grafanaGlobalStyles.css';

const LazyIncidentPage = React.lazy(() => import('pages/incident/Incident'));
const LazyEscalationChainsPage = React.lazy(() => import('pages/escalation-chains/EscalationChains'));
const LazyIncidentsPage = React.lazy(() => import('pages/incidents/Incidents'));
const LazyIntegrationPage = React.lazy(() => import('pages/integration/Integration'));
const LazyIntegrationsPage = React.lazy(() => import('pages/integrations/Integrations'));
const LazyOutgoingWebhooksPage = React.lazy(() => import('pages/outgoing_webhooks/OutgoingWebhooks'));
const LazySchedulePage = React.lazy(() => import('pages/schedule/Schedule'));
const LazySchedulesPage = React.lazy(() => import('pages/schedules/Schedules'));
const LazyUsersPage = React.lazy(() => import('pages/users/Users'));
const LazyChatOpsPage = React.lazy(() => import('pages/settings/tabs/ChatOps/ChatOps'));
const LazySettingsPage = React.lazy(() => import('pages/settings/SettingsPage'));
const LazyLiveSettings = React.lazy(() => import('pages/settings/tabs/LiveSettings/LiveSettingsPage'));
const LazyCloudPage = React.lazy(() => import('pages/settings/tabs/Cloud/CloudPage'));
const LazyInsights = React.lazy(() => import('pages/insights/Insights'));

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
      <React.Suspense fallback={<LoadingPlaceholder text="Loading..." />}>
        <div
          className={cx(
            css`
              position: relative;
              flex-grow: 1;
            `
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
                    <Route path=":id" element={<LazyIncidentPage query={query} />} />
                    <Route index element={<LazyIncidentsPage query={query} />} />
                  </Route>

                  <Route path="users">
                    <Route path=":id" element={<LazyUsersPage query={query} />} />
                    <Route index element={<LazyUsersPage query={query} />} />
                  </Route>

                  <Route path="integrations">
                    <Route path=":id" element={<LazyIntegrationPage query={query} />} />
                    <Route index element={<LazyIntegrationsPage query={query} />} />
                  </Route>

                  <Route path="escalations">
                    <Route path=":id" element={<LazyEscalationChainsPage query={query} />} />
                    <Route index element={<LazyEscalationChainsPage query={query} />} />
                  </Route>

                  <Route path="schedules">
                    <Route path=":id" element={<LazySchedulePage query={query} />} />
                    <Route index element={<LazySchedulesPage query={query} />} />
                  </Route>

                  <Route path="outgoing_webhooks">
                    <Route path=":action/:id" element={<LazyOutgoingWebhooksPage query={query} />} />
                    <Route path=":id" element={<LazyOutgoingWebhooksPage query={query} />} />
                    <Route index element={<LazyOutgoingWebhooksPage query={query} />} />
                  </Route>

                  <Route path="settings" element={<LazySettingsPage />} />
                  <Route path="chat-ops" element={<LazyChatOpsPage query={query} />} />
                  <Route path="live-settings" element={<LazyLiveSettings />} />
                  <Route path="cloud" element={<LazyCloudPage />} />
                  <Route path="insights" element={<LazyInsights />} />

                  <Route path="incident" element={<Navigate to="alert-group" replace />} />
                  <Route path="incidents" element={<Navigate to="alert-groups" replace />} />

                  <Route path="*" element={<NoMatch />} />
                </Routes>
              )}
            />
          </RenderConditionally>
        </div>
      </React.Suspense>
    </DefaultPageLayout>
  );
});
