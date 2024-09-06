import React, { useEffect, useState } from 'react';

import { Button, LoadingPlaceholder, Stack } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

interface CloudPhoneSettingsProps extends WithStoreProps {
  userPk?: ApiSchemas['User']['pk'];
}

const _CloudPhoneSettings = observer((props: CloudPhoneSettingsProps) => {
  const { userPk } = props;
  const store = useStore();
  const [syncing, setSyncing] = useState<boolean>(false);
  const [userStatus, setUserStatus] = useState<number>(0);
  const [userLink, setUserLink] = useState<string>(null);

  const email = store.userStore.items[userPk].email;

  useEffect(() => {
    getCloudUserInfo();
  }, []);

  const handleLinkClick = (link: string) => {
    window.open(link, '_blank');
  };

  const syncUser = async () => {
    setSyncing(true);
    await store.cloudStore.syncCloudUser(userPk);
    const cloudUser = await store.cloudStore.getCloudUser(userPk);
    setUserStatus(cloudUser?.cloud_data?.status);
    setUserLink(cloudUser?.cloud_data?.link);
    setSyncing(false);
  };

  const getCloudUserInfo = async () => {
    const cloudUser = await store.cloudStore.getCloudUser(userPk);
    setUserStatus(cloudUser?.cloud_data?.status);
    setUserLink(cloudUser?.cloud_data?.link);
  };

  const UserCloudStatus = () => {
    switch (userStatus) {
      case 0:
        return (
          <Stack direction="column" gap={StackSize.lg}>
            <Text>Cloud notifications enabled, but Grafana Cloud OnCall instance is not connected.</Text>
            <PluginLink query={{ page: 'cloud' }}>
              <Button variant="secondary" icon="external-link-alt">
                Open Grafana Cloud OnCall page
              </Button>
            </PluginLink>
          </Stack>
        );
      case 1:
        return (
          <Stack direction="column" gap={StackSize.lg}>
            <Text>
              We can’t find a matching account in the connected Grafana Cloud OnCall instance (matching by e-mail
              {email && ': ' + email}).
            </Text>
            <Button variant="primary" onClick={() => handleLinkClick(userLink)}>
              Sign up in Grafana Cloud OnCall
            </Button>
          </Stack>
        );
      case 2:
        return (
          <Stack direction="column" gap={StackSize.lg}>
            <Text>
              Your account successfully matched with the Grafana Cloud OnCall account. Please verify your phone number.{' '}
            </Text>
            <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(userLink)}>
              Verify phone number in Grafana Cloud OnCall
            </Button>
          </Stack>
        );
      case 3:
        return (
          <Stack direction="column" gap={StackSize.lg}>
            <Text>
              Your account successfully matched with the Grafana Cloud OnCall account. Your phone number is verified.{' '}
            </Text>
            <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(userLink)}>
              Open account in Grafana Cloud OnCall
            </Button>
          </Stack>
        );
      default:
        return (
          <Stack direction="column" gap={StackSize.lg}>
            <Text>
              We can’t find a matching account in the connected Grafana Cloud OnCall instance (matching by e-mail
              {email && ': ' + email}).
            </Text>
            <Button variant="primary" onClick={() => handleLinkClick(userLink)}>
              Sign up in Grafana Cloud OnCall
            </Button>
          </Stack>
        );
    }
  };

  return (
    <WithPermissionControlDisplay
      userAction={UserActions.UserSettingsWrite}
      title="OnCall uses Grafana Cloud OnCall for SMS and phone call notifications"
    >
      <Stack direction="column" gap={StackSize.lg}>
        <Text.Title level={3}>OnCall uses Grafana Cloud OnCall for SMS and phone call notifications</Text.Title>
        {syncing ? (
          <Button icon="sync" variant="secondary" disabled>
            Updating...
          </Button>
        ) : (
          <Button icon="sync" variant="secondary" onClick={syncUser} disabled={userStatus === 0}>
            Reload from Cloud
          </Button>
        )}
        {!syncing ? <UserCloudStatus /> : <LoadingPlaceholder text="Loading..." />}
      </Stack>
    </WithPermissionControlDisplay>
  );
});

export const CloudPhoneSettings = withMobXProviderContext(_CloudPhoneSettings);
