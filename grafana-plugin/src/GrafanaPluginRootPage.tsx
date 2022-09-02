import React, { useEffect, useMemo } from 'react';

import { AppRootProps } from '@grafana/data';
import { Button, HorizontalGroup, LinkButton, VerticalGroup } from '@grafana/ui';
import { observer, Provider } from 'mobx-react';

import 'interceptors';

import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import logo from 'img/logo.svg';
import { pages } from 'pages';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { useNavModel } from 'utils/hooks';

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
    useMemo(
      () => ({
        page,
        pages,
        path: pathWithoutLeadingSlash,
        meta,
        grafanaUser: window.grafanaBootData.user,
        enableLiveSettings: store.hasFeature(AppFeature.LiveSettings),
        enableCloudPage: store.hasFeature(AppFeature.CloudConnection),
        backendLicense,
      }),
      [meta, pathWithoutLeadingSlash, page, store.features]
    )
  );
  useEffect(() => {
    /* @ts-ignore */
    onNavChanged(navModel);
  }, [navModel, onNavChanged]);

  const Page = pages.find(({ id }) => id === page)?.component || pages[0].component;

  return (
    <DefaultPageLayout {...props}>
      <GrafanaTeamSelect />
      <Page {...props} path={pathWithoutLeadingSlash} />
    </DefaultPageLayout>
  );
});
