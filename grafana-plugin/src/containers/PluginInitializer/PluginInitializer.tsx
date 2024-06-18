import React, { FC } from 'react';

import { Button, HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import { observer } from 'mobx-react';
import { useHistory } from 'react-router-dom';

import { FullPageError } from 'components/FullPageError/FullPageError';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { REQUEST_HELP_URL, PLUGIN_ID } from 'utils/consts';
import { useInitializePlugin } from 'utils/hooks';
import { getIsRunningOpenSourceVersion } from 'utils/utils';

interface PluginInitializerProps {
  children: React.ReactNode;
}

export const PluginInitializer: FC<PluginInitializerProps> = observer(({ children }) => {
  const { isInitialized, isPluginInitializing } = useInitializePlugin();

  if (isPluginInitializing) {
    return <LoadingPlaceholder text="Loading..." />;
  }
  return (
    <RenderConditionally
      shouldRender={isInitialized}
      backupChildren={<PluginNotInitializedFullPageError />}
      render={() => <>{children}</>}
    />
  );
});

const PluginNotInitializedFullPageError = observer(() => {
  const isOpenSource = getIsRunningOpenSourceVersion();
  const isCurrentUserAdmin = window.grafanaBootData.user.orgRole === 'Admin';
  const { push } = useHistory();

  const getSubtitleExtension = () => {
    if (!isOpenSource) {
      return 'request help from our support team.';
    }
    return isCurrentUserAdmin
      ? 'go to plugin configuration page to check what went wrong.'
      : 'contact your administrator to check what went wrong.';
  };

  return (
    <FullPageError
      title="Plugin not initialized"
      subtitle={`Looks like OnCall plugin is not configured properly and couldn't be loaded. Retry or ${getSubtitleExtension()}`}
    >
      <HorizontalGroup>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Retry
        </Button>
        {!isOpenSource && <Button onClick={() => window.open(REQUEST_HELP_URL, '_blank')}>Request help</Button>}
        {isOpenSource && isCurrentUserAdmin && (
          <Button onClick={() => push(`/plugins/${PLUGIN_ID}`)}>Open configuration</Button>
        )}
      </HorizontalGroup>
    </FullPageError>
  );
});
