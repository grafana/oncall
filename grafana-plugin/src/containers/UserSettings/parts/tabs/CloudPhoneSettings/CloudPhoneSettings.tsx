import React, { useEffect, useState, useCallback } from 'react';

import { Button, HorizontalGroup, VerticalGroup, LoadingPlaceholder } from '@grafana/ui';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

interface CloudPhoneSettingsProps extends WithStoreProps {
  userPk?: User['pk'];
}

const CloudPhoneSettings = observer(({ userPk }: CloudPhoneSettingsProps) => {
  const {
    cloudStore: { getCloudUser, syncCloudUser },
    hasFeature,
    isUserActionAllowed,
  } = useStore();
  const [syncing, setSyncing] = useState<boolean>(false);
  const [userStatus, setUserStatus] = useState<number>(0);
  const [userLink, setUserLink] = useState<string>(null);

  const getCloudUserInfo = useCallback(async () => {
    const cloudUser = await getCloudUser(userPk);
    setUserStatus(cloudUser?.cloud_data?.status);
    setUserLink(cloudUser?.cloud_data?.link);
  }, [getCloudUser, userPk]);

  const handleLinkClick = useCallback((link: string) => {
    window.open(link, '_blank');
  }, []);

  const syncUser = useCallback(async () => {
    setSyncing(true);

    await syncCloudUser(userPk);
    const cloudUser = await getCloudUser(userPk);

    setUserStatus(cloudUser?.cloud_data?.status);
    setUserLink(cloudUser?.cloud_data?.link);
    setSyncing(false);
  }, [syncCloudUser, getCloudUser, userPk]);

  useEffect(() => {
    getCloudUserInfo();
  }, [getCloudUserInfo]);

  const UserCloudStatus = () => {
    switch (userStatus) {
      case 0:
        if (hasFeature(AppFeature.CloudNotifications)) {
          return (
            <VerticalGroup spacing="lg">
              <Text>Your account successfully matched, but Cloud is not connected. </Text>
              <PluginLink query={{ page: 'cloud' }}>
                <Button variant="secondary" icon="external-link-alt">
                  Open Grafana Cloud page
                </Button>
              </PluginLink>
            </VerticalGroup>
          );
        }
        return (
          <VerticalGroup spacing="lg">
            <Text>Grafana Cloud is not synced</Text>
          </VerticalGroup>
        );
      case 1:
        return (
          <VerticalGroup spacing="lg">
            <Text>
              {
                'We can’t find a matching account in the connected Grafana Cloud instance (matching happens by e-mail). '
              }
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
              {
                'We can’t find a matching account in the connected Grafana Cloud instance (matching happens by e-mail). '
              }
            </Text>
            <Button variant="primary" onClick={() => handleLinkClick(userLink)}>
              Sign up in Grafana Cloud
            </Button>
          </VerticalGroup>
        );
    }
  };

  return (
    <>
      {isUserActionAllowed(UserAction.UpdateOtherUsersSettings) ? (
        <VerticalGroup spacing="lg">
          <HorizontalGroup justify="space-between">
            <Text.Title level={3}>OnCall use Grafana Cloud for SMS and phone call notifications</Text.Title>
            {syncing ? (
              <Button variant="secondary" icon="sync" disabled>
                Updating...
              </Button>
            ) : (
              <Button variant="secondary" icon="sync" onClick={syncUser} disabled={userStatus === 0}>
                Update
              </Button>
            )}
          </HorizontalGroup>
          {!syncing ? <UserCloudStatus /> : <LoadingPlaceholder text="Loading..." />}
        </VerticalGroup>
      ) : (
        <VerticalGroup spacing="lg">
          <Text.Title level={3}>OnCall use Grafana Cloud for SMS and phone call notifications</Text.Title>
          <Text>You do not have permission to perform this action. Ask an admin to upgrade your permissions.</Text>
        </VerticalGroup>
      )}
    </>
  );
});

export default withMobXProviderContext(CloudPhoneSettings);
