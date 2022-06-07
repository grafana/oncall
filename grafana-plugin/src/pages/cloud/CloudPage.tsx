import React, { useCallback, useEffect, useState } from 'react';

import { getLocationSrv, LocationUpdate } from '@grafana/runtime';
import { Field, Input, Button, Modal, HorizontalGroup, Alert, Icon, VerticalGroup, Table } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { CrossCircleIcon, HeartIcon } from 'icons';
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
    store.cloudStore.getCloudConnectionStatus().then((cloudStatus) => {
      setCloudIsConnected(cloudStatus.cloud_connection_status);
    });
  }, []);

  const data = [
    { id: 'yshanyrova', email: 'y.shanyrova@grafana.com', cloud_data: { status: 2, link: '/test/abc' } },
    { id: 'amixradmin', email: 'amixr-admin@grafana.com', cloud_data: { status: 1, link: '/test/abc' } },
    { id: 'amixr', email: 'amixr@grafana.com', cloud_data: { status: undefined, link: '/test/abc' } },
  ];

  // const { count, results } = store.cloudStore.getSearchResult();

  const handleChangeCloudApiKey = useCallback((e) => {
    setCloudApiKey(e.target.value);
  }, []);

  const saveKeyAndConnect = () => {
    setShowConfirmationModal(true);
  };

  const disconnectCloudOncall = () => {
    console.log('disconnected');
    setCloudIsConnected(false);
    store.cloudStore.disconnectToCloud();
  };

  const connectToCloud = () => {
    setCloudIsConnected(true);
    setShowConfirmationModal(false);
    // store.cloudStore.update('')
    store.cloudStore.connectToCloud(cloudApiKey);
  };

  const syncUsers = () => {
    store.cloudStore.syncCloudUsers();
  };

  const handleLinkClick = (link: string) => {
    getLocationSrv().update({ partial: false, path: link });
  };

  const renderButtons = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
      case 0:
        return null;
      case 1:
        return (
          <Button
            variant="secondary"
            icon="external-link-alt"
            size="sm"
            className={cx('table-button')}
            onClick={() => handleLinkClick(user?.cloud_data?.link)}
          >
            Configure notifications
          </Button>
        );
      case 2:
        return (
          <Button
            variant="secondary"
            icon="external-link-alt"
            size="sm"
            className={cx('table-button')}
            onClick={() => handleLinkClick(user?.cloud_data?.link)}
          >
            Open profile in Cloud
          </Button>
        );
      default:
        return null;
    }
  };

  const renderStatus = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
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
    switch (user?.cloud_data?.status) {
      case 0:
        return (
          <span className={cx('error-message')}>
            <CrossCircleIcon />
          </span>
        );
      case 1:
        return <Icon className={cx('success-message')} name="check-circle" />;

      case 2:
        return <Icon className={cx('warning-message')} name="exclamation-triangle" />;
      default:
        return (
          <span className={cx('error-message')}>
            <CrossCircleIcon />
          </span>
        );
    }
  };

  const renderEmail = (user: Cloud) => {
    return <Text type="primary">{user.email}</Text>;
  };

  const columns = [
    {
      width: '2%',
      render: renderStatusIcon,
      key: 'statusIcon',
    },
    {
      width: '28%',
      render: renderEmail,
      key: 'email',
    },
    {
      width: '50%',
      render: renderStatus,
      key: 'status',
    },
    {
      width: '20%',
      render: renderButtons,
      key: 'buttons',
      align: 'actions',
    },
  ];

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="lg">
        <Text.Title level={3} className={cx('cloud-page-title')}>
          Connect Open Source OnCall and <Text className={cx('cloud-oncall-name')}>Cloud OnCall</Text>
        </Text.Title>
        <Block withBackground bordered className={cx('info-block')}>
          {cloudIsConnected ? (
            <VerticalGroup>
              <Text.Title level={4}>
                <Icon name="check" className={cx('block-icon')} size="lg" /> Cloud OnCall API key
              </Text.Title>
              <Text type="secondary">Cloud OnCall is sucessfully connected.</Text>

              <WithConfirm title="Are you sure to disconnect Cloud OnCall?" confirmText="Disconnect">
                <Button variant="destructive" onClick={disconnectCloudOncall} size="md" className={cx('block-button')}>
                  Disconnect
                </Button>
              </WithConfirm>
            </VerticalGroup>
          ) : (
            <VerticalGroup>
              <Text.Title level={4}>
                <Icon name="sync" className={cx('block-icon')} size="lg" /> Cloud OnCall API key
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
              <span className={cx('block-icon')}>
                <HeartIcon />
              </span>{' '}
              Monitor cloud instance with heartbeat
            </Text.Title>
            <Text type="secondary">
              Once connected, current OnCall instance will send heartbeats every 3 minutes to the cloud Instance. If no
              heartbeat will be received in 10 minutes, cloud instance will issue an alert.
            </Text>
            {cloudIsConnected && (
              <Button
                variant="secondary"
                icon="external-link-alt"
                className={cx('block-button')}
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
              <Icon name="bell" className={cx('block-icon')} size="lg" /> SMS and phone call notifications
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
                  showHeader={false}
                  emptyText={data ? 'No variables found' : 'Loading...'}
                  title={() => (
                    <div className={cx('table-title')}>
                      <HorizontalGroup justify="space-between">
                        <Text type="secondary">
                          {/* {count ? count : 0} */}
                          {`3 users matched between OSS and Cloud OnCall`}
                        </Text>
                        <Button variant="primary" onClick={syncUsers} icon="sync">
                          Sync users
                        </Button>
                      </HorizontalGroup>
                    </div>
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
