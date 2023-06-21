import React, { FC, PropsWithChildren, useCallback, useEffect } from 'react';

import { PluginPage as RealPluginPage } from '@grafana/runtime'; // Use the one from @grafana, not our wrapped PluginPage
import { Button, HorizontalGroup, LinkButton } from '@grafana/ui';
import { PluginPageFallback } from 'PluginPage';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import logo from 'img/logo.svg';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';

export type PluginSetupProps = AppRootProps & {
  InitializedComponent: (props: AppRootProps) => JSX.Element;
};

type PluginSetupWrapperProps = PropsWithChildren<{
  text: string;
}>;

const PluginSetupWrapper: FC<PluginSetupWrapperProps> = ({ text, children }) => {
  const PluginPage = (isTopNavbar() ? RealPluginPage : PluginPageFallback) as React.ComponentType<any>;

  return (
    <PluginPage>
      <div className="spin">
        <img alt="Grafana OnCall Logo" src={logo} />
        <div className="spin-text">{text}</div>
        {children}
      </div>
    </PluginPage>
  );
};

const PluginSetup: FC<PluginSetupProps> = observer(({ InitializedComponent, ...props }) => {
  const store = useStore();
  const setupPlugin = useCallback(() => store.setupPlugin(props.meta), [props.meta]);

  useEffect(() => {
    setupPlugin();
  }, [setupPlugin]);

  if (store.appLoading) {
    return <PluginSetupWrapper text="Initializing plugin..." />;
  }

  if (store.initializationError) {
    return (
      <PluginSetupWrapper text={store.initializationError}>
        {!store.currentlyUndergoingMaintenance && (
          <div className="configure-plugin">
            <HorizontalGroup>
              <Button variant="primary" onClick={setupPlugin} size="sm">
                Retry
              </Button>
              <LinkButton href={`/plugins/grafana-oncall-app?page=configuration`} variant="primary" size="sm">
                Configure Plugin
              </LinkButton>
            </HorizontalGroup>
          </div>
        )}
      </PluginSetupWrapper>
    );
  }

  return <InitializedComponent {...props} />;
});

export default PluginSetup;
