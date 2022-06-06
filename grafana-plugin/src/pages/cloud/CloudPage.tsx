import React, { useCallback, useEffect, useState } from 'react';

import { getLocationSrv, LocationUpdate } from '@grafana/runtime';
import { Field, Input, Button, Modal, HorizontalGroup, Alert, Icon, VerticalGroup, Table } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { Cloud } from 'models/cloud/cloud.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import styles from './CloudPage.module.css';

const cx = cn.bind(styles);

interface CloudPageProps extends WithStoreProps {}

const CloudPage = (props: CloudPageProps) => {
  const store = useStore();
  const [cloudApiKey, setCloudApiKey] = useState<string>('');
  const [cloudIsConnected, setCloudIsConnected] = useState<boolean>(true);
  const [showConfirmationModal, setShowConfirmationModal] = useState<boolean>(false);

  useEffect(() => {
    store.cloudStore.updateItems();
  }, []);

  const usersCount = 3;
  const data = [
    { id: 'yshanyrova', username: 'y.shanyrova@grafana.com', cloud_sync_status: 2, link: '/test/abc' },
    { id: 'amixradmin', username: 'amixr-admin@grafana.com', cloud_sync_status: 1, link: '/test/qwerty' },
    { id: 'amixr', username: 'amixr@grafana.com', cloud_sync_status: undefined, link: undefined },
  ];

  // const data = store.cloudStore.getSearchResult();
  const handleChangeCloudApiKey = useCallback((e) => {
    setCloudApiKey(e.target.value);
  }, []);

  const saveKeyAndConnect = () => {
    setShowConfirmationModal(true);
  };

  const disconnectCloudOncall = () => {
    console.log('disconnected');
    setCloudIsConnected(false);
  };

  const connectToCloud = () => {
    console.log('CONNECT TO CLOUD');
    setCloudIsConnected(true);
    setShowConfirmationModal(false);
  };

  const syncUsers = () => {
    console.log('Sync Users');
  };

  const handleLinkClick = (link: string) => {
    getLocationSrv().update({ partial: false, path: link });
  };

  const renderButtons = (user: Cloud) => {
    switch (user.cloud_sync_status) {
      case 0:
        return null;
      case 1:
        return (
          <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(user.link)}>
            Configure notifications
          </Button>
        );
      case 2:
        return (
          <Button variant="secondary" icon="external-link-alt" onClick={() => handleLinkClick(user.link)}>
            Open profile in Cloud
          </Button>
        );
      default:
        return null;
    }
  };

  const renderStatus = (user: Cloud) => {
    switch (user.cloud_sync_status) {
      case 0:
        return <Text className={cx('error-message')}>User not found in the Grafana Cloud</Text>;
      case 1:
        return <Text type="success">Phone number verified</Text>;

      case 2:
        return <Text type="warning">Phone number is not verified in Grafana Cloud</Text>;
      default:
        return <Text className={cx('error-message')}>User not found in Grafana Cloud</Text>;
    }
  };

  const renderStatusIcon = (user: Cloud) => {
    switch (user.cloud_sync_status) {
      case 0:
        return <Icon className={cx('error-message')} name="times" />;
      case 1:
        return <Icon className={cx('success-message')} name="check-circle" />;

      case 2:
        return <Icon className={cx('warning-message')} name="exclamation-triangle" />;
      default:
        return <Icon className={cx('error-message')} name="times" />;
    }
  };

  const renderEmail = (user: Cloud) => {
    return <Text type="primary">{user.username}</Text>;
  };

  const columns = [
    {
      width: '5%',
      render: renderStatusIcon,
      key: 'statusIcon',
    },
    {
      width: '30%',
      render: renderEmail,
      key: 'email',
    },
    {
      width: '35%',
      render: renderStatus,
      key: 'status',
    },
    {
      width: '30%',
      render: renderButtons,
      key: 'buttons',
      align: 'actions',
    },
  ];

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="lg">
        <Text.Title level={3}>
          Connect Open Source OnCall and <Text className={cx('cloud-oncall-name')}>Cloud OnCall</Text>
        </Text.Title>
        <Block withBackground bordered className={cx('info-block')}>
          {cloudIsConnected ? (
            <VerticalGroup>
              <Text.Title level={4}>
                <Icon name="check" className={cx('heart-icon')} /> Cloud OnCall API key
              </Text.Title>
              <Text type="secondary">Cloud OnCall is sucessfully connected.</Text>

              <WithConfirm title="Are you sure to disconnect Cloud OnCall?" confirmText="Disconnect">
                <Button variant="destructive" onClick={disconnectCloudOncall} size="md">
                  Disconnect
                </Button>
              </WithConfirm>
            </VerticalGroup>
          ) : (
            <VerticalGroup>
              <Text.Title level={4}>
                <Icon name="sync" className={cx('heart-icon')} /> Cloud OnCall API key
              </Text.Title>
              <Field label="" description="Find it in you Cloud OnCall -> Settings page" style={{ width: '100%' }}>
                <Input id="cloudApiKey" onChange={handleChangeCloudApiKey} />
              </Field>
              <Button variant="primary" onClick={saveKeyAndConnect} disabled={!cloudApiKey} size="md">
                Save key and connect
              </Button>
            </VerticalGroup>
          )}
        </Block>

        {showConfirmationModal && (
          <Modal
            isOpen
            title="Are you sure you want to connect to cloud?"
            onDismiss={() => setShowConfirmationModal(false)}
          >
            <HorizontalGroup>
              <Button variant="primary" onClick={connectToCloud}>
                Continue
              </Button>
              <Button variant="secondary" onClick={() => setShowConfirmationModal(false)}>
                Cancel
              </Button>
            </HorizontalGroup>
          </Modal>
        )}

        <Block bordered withBackground className={cx('info-block')}>
          <VerticalGroup>
            <Text.Title level={4}>
              <Icon name="heart-break" className={cx('heart-icon')} /> Monitor cloud instance with heartbeat
            </Text.Title>
            <Text type="secondary">
              Once connected, current OnCall instance will send heartbeats every 3 minutes to the cloud Instance. If no
              heartbeat will be received in 10 minutes, cloud instance will issue an alert.
            </Text>
            {cloudIsConnected && (
              <Button
                variant="secondary"
                icon="external-link-alt"
                onClick={() => handleLinkClick('fillmewithcorrectlink')}
              >
                Configure escalations in Cloud OnCall
              </Button>
            )}
          </VerticalGroup>
        </Block>

        <Block bordered withBackground className={cx('info-block')}>
          <VerticalGroup>
            <Text.Title level={4}>
              <Icon name="bell" /> SMS and phone call notifications
            </Text.Title>
            {cloudIsConnected ? (
              <div style={{ width: '100%' }}>
                <Text type="secondary">
                  {
                    'Ask your users to sign up in Grafana Cloud, verify phone number and feel free to set up SMS & phone call notificaitons in personal settings!'
                  }
                </Text>

                <GTable
                  className={cx('user-table')}
                  rowClassName={cx('user-row')}
                  emptyText={data ? 'No variables found' : 'Loading...'}
                  title={() => (
                    <HorizontalGroup justify="space-between">
                      <Text type="secondary">{`${usersCount} users matched between OSS and Cloud OnCall`}</Text>
                      <Button variant="primary" onClick={syncUsers} icon="sync">
                        Sync users
                      </Button>
                    </HorizontalGroup>
                  )}
                  rowKey="id"
                  // @ts-ignore
                  columns={columns}
                  data={data}
                />
              </div>
            ) : (
              <Text type="secondary">Users matched between OSS and Cloud OnCall currently unavialable.</Text>
            )}
          </VerticalGroup>
        </Block>
      </VerticalGroup>
    </div>
  );
};

export default withMobXProviderContext(CloudPage);
