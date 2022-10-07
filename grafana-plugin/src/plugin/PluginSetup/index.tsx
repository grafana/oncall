import React, { FC, PropsWithChildren, useCallback, useEffect } from 'react';

import { Button, HorizontalGroup, LinkButton } from '@grafana/ui';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import logo from 'img/logo.svg';
import { useStore } from 'state/useStore';

export type PluginSetupProps = AppRootProps & {
  InitializedComponent: (props: AppRootProps) => JSX.Element;
};

type PluginSetupWrapperProps = PropsWithChildren<{
  text: string;
}>;

const PluginSetupWrapper: FC<PluginSetupWrapperProps> = ({ text, children }) => (
  <div className="spin">
    <img alt="Grafana OnCall Logo" src={logo} />
    <div className="spin-text">{text}</div>
    {children}
  </div>
);

export const PluginSetup: FC<PluginSetupProps> = ({ InitializedComponent, ...props }): React.ReactElement => {
  const store = useStore();
  const setupPlugin = useCallback(() => store.setupPlugin(props.meta), [props.meta]);

  useEffect(() => {
    setupPlugin();
  }, []);

  if (store.appLoading) {
    return <PluginSetupWrapper text="Initializing plugin..." />;
  }

  if (store.initializationError) {
    return (
      <PluginSetupWrapper text={store.initializationError}>
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
      </PluginSetupWrapper>
    );
  }

  return <InitializedComponent {...props} />;
};

export default observer(PluginSetup);
