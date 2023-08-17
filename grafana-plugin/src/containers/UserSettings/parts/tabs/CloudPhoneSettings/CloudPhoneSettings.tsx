import React, { useEffect, useState } from 'react';

import { Button, VerticalGroup, LoadingPlaceholder } from '@grafana/ui';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { User } from 'models/user/user.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

interface CloudPhoneSettingsProps extends WithStoreProps {
  userPk?: User['pk'];
}

const CloudPhoneSettings = observer((props: CloudPhoneSettingsProps) => {
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
          <VerticalGroup spacing="lg">
            <Text>Cloud notifications enabled, but Grafana Cloud instance is not connected.</Text>
            <PluginLink query={{ page: 'cloud' }}>
              <Button variant="secondary" icon="external-link-alt">
                Open Grafana Cloud page
              </Button>
            </PluginLink>
          </VerticalGroup>
        );
      case 1:
        return (
          <VerticalGroup spacing="lg">
            <Text>
              We can’t find a matching account in the connected Grafana Cloud instance (matching by e-mail
              {email && ': ' + email}).
            </Text>
            <Button variant="primary" onClick={() => handleLinkClick(userLink)}>
              Sign up in Grafana Cloud
            </Button>
          </VerticalGroup>
        );
      case 2:
        return (
          <VerticalGroup spacing="lg">
            <Text>
              Your account successfully matched with the Grafana Cloud account. Please verify your phone number.{' '}
            </Text>
            <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(userLink)}>
              Verify phone number in Grafana Cloud
            </Button>
          </VerticalGroup>
        );
      case 3:
        return (
          <VerticalGroup spacing="lg">
            <Text>
              Your account successfully matched with the Grafana Cloud account. Your phone number is verified.{' '}
            </Text>
            <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(userLink)}>
              Open account in Grafana Cloud
            </Button>
          </VerticalGroup>
        );
      default:
        return (
          <VerticalGroup spacing="lg">
            <Text>
              We can’t find a matching account in the connected Grafana Cloud instance (matching by e-mail
              {email && ': ' + email}).
            </Text>
            <Button variant="primary" onClick={() => handleLinkClick(userLink)}>
              Sign up in Grafana Cloud
            </Button>
          </VerticalGroup>
        );
    }
  };

  return (
    <WithPermissionControlDisplay
      userAction={UserActions.UserSettingsWrite}
      title="OnCall uses Grafana Cloud for SMS and phone call notifications"
    >
      <VerticalGroup spacing="lg">
        <Text.Title level={3}>OnCall uses Grafana Cloud for SMS and phone call notifications</Text.Title>
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
      </VerticalGroup>
    </WithPermissionControlDisplay>
  );
});

export default withMobXProviderContext(CloudPhoneSettings);
