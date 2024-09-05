import React, { FC } from 'react';

import { Button, Stack, LoadingPlaceholder } from '@grafana/ui';
import { REQUEST_HELP_URL, PLUGIN_CONFIG } from 'helpers/consts';
import { useInitializePlugin } from 'helpers/hooks';
import { getIsRunningOpenSourceVersion } from 'helpers/utils';
import { observer } from 'mobx-react';
import { useNavigate } from 'react-router-dom-v5-compat';

import { FullPageError } from 'components/FullPageError/FullPageError';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';

interface PluginInitializerProps {
  children: React.ReactNode;
}

export const PluginInitializer: FC<PluginInitializerProps> = observer(({ children }) => {
  const { isConnected, isCheckingConnectionStatus } = useInitializePlugin();

  if (isCheckingConnectionStatus) {
    return (
      <Stack direction="column" justifyContent="center" height="100%" alignItems="center">
        <LoadingPlaceholder text="Loading..." />
      </Stack>
    );
  }
  return (
    <RenderConditionally
      shouldRender={isConnected}
      backupChildren={<PluginNotConnectedFullPageError />}
      render={() => <>{children}</>}
    />
  );
});

const PluginNotConnectedFullPageError = observer(() => {
  const isOpenSource = getIsRunningOpenSourceVersion();
  const isCurrentUserAdmin = window.grafanaBootData.user.orgRole === 'Admin';
  const navigate = useNavigate();

  const getSubtitleExtension = () => {
    if (!isOpenSource) {
      return 'request help from our support team.';
    }
    return isCurrentUserAdmin
      ? 'go to plugin configuration page to establish connection.'
      : 'contact your administrator.';
  };

  return (
    <FullPageError
      title="Plugin not connected"
      subtitle={
        <>
          Looks like OnCall plugin hasn't been connected yet or has been misconfigured. <br />
          Retry or {getSubtitleExtension()}
        </>
      }
    >
      <Stack>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Retry
        </Button>
        {!isOpenSource && <Button onClick={() => window.open(REQUEST_HELP_URL, '_blank')}>Request help</Button>}
        {isOpenSource && isCurrentUserAdmin && (
          <Button onClick={() => navigate(PLUGIN_CONFIG)}>Open configuration</Button>
        )}
      </Stack>
    </FullPageError>
  );
});
