import React, { useCallback, useEffect, useState } from 'react';

import { getLocationSrv, LocationUpdate } from '@grafana/runtime';
import {
  Field,
  Input,
  Button,
  Modal,
  HorizontalGroup,
  Alert,
  Icon,
  VerticalGroup,
  Table,
  LoadingPlaceholder,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './CloudPhoneSettings.module.css';

const cx = cn.bind(styles);

interface CloudPhoneSettingsProps extends WithStoreProps {
  userPk?: User['pk'];
}

const CloudPhoneSettings = observer((props: CloudPhoneSettingsProps) => {
  const { userPk } = props;
  const store = useStore();
  const [syncing, setSyncing] = useState<boolean>(false);
  const [userStatus, setUserStatus] = useState<number>(0);
  const [userLink, setUserLink] = useState<string>(null);

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
        if (store.hasFeature(AppFeature.CloudNotifications)) {
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
      {store.isUserActionAllowed(UserAction.UpdateOtherUsersSettings) ? (
        <VerticalGroup spacing="lg">
          <HorizontalGroup justify="space-between">
            <Text.Title level={3}>OnCall use Grafana Cloud for SMS and phone call notifications</Text.Title>
            {syncing ? (
              <Button variant="secondary" icon="sync" disabled>
                Updating...
              </Button>
            ) : (
              <Button variant="secondary" icon="sync" onClick={syncUser}>
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
