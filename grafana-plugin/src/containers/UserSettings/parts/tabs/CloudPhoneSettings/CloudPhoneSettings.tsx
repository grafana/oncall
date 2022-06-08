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
import { User as UserType } from 'models/user/user.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import styles from './CloudPhoneSettings.module.css';

const cx = cn.bind(styles);

interface CloudPhoneSettingsProps extends WithStoreProps {}

const CloudPhoneSettings = observer((props: CloudPhoneSettingsProps) => {
  const store = useStore();
  const [isAccountMatched, setIsAccountMatched] = useState<boolean>(true);
  const [isPhoneVerified, setIsPhoneVerified] = useState<boolean>(true);
  const [userStatus, setUserStatus] = useState<number>(0);
  const [userLink, setUserLink] = useState<string>(null);

  useEffect(() => {
    getCloudUserInfo();
  }, []);

  const handleLinkClick = (link: string) => {
    getLocationSrv().update({ partial: false, path: link });
  };

  const syncUser = () => {
    store.cloudStore.syncCloudUser(store.userStore.currentUserPk);
  };

  const getCloudUserInfo = async () => {
    await store.cloudStore.updateItems();
    const { count, results } = await store.cloudStore.getSearchResult();
    console.log('RES', results);
    const cloudUser =
      results && (await results.find((element: { id: string }) => element.id === store.userStore.currentUserPk));
    console.log('CLOUD USER', cloudUser);
    setUserStatus(cloudUser?.cloud_data?.status);
    setUserLink(cloudUser?.cloud_data?.link);
  };

  const UserCloudStatus = () => {
    switch (userStatus) {
      case 0:
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
    <VerticalGroup spacing="lg">
      <HorizontalGroup justify="space-between">
        <Text.Title level={3}>OnCall use Grafana Cloud for SMS and phone call notifications</Text.Title>
        <Button variant="secondary" icon="sync" onClick={syncUser}>
          Update
        </Button>
      </HorizontalGroup>
      {userStatus ? <UserCloudStatus /> : <LoadingPlaceholder text="Loading..." />}
    </VerticalGroup>
  );
});

export default withMobXProviderContext(CloudPhoneSettings);
