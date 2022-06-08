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
import { CrossCircleIcon, HeartIcon } from 'icons';
import { Cloud } from 'models/cloud/cloud.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openErrorNotification } from 'utils';

import styles from './CloudPage.module.css';

const cx = cn.bind(styles);

interface CloudPageProps extends WithStoreProps {}
const ITEMS_PER_PAGE = 50;

const CloudPage = observer((props: CloudPageProps) => {
  const store = useStore();
  const [page, setPage] = useState<number>(1);
  const [cloudApiKey, setCloudApiKey] = useState<string>('');
  const [apiKeyError, setApiKeyError] = useState<boolean>(false);
  const [cloudIsConnected, setCloudIsConnected] = useState<boolean>(undefined);
  const [heartbitLink, setHeartbitLink] = useState<string>(null);
  const [heartbitStatus, setHeartbitStatus] = useState<boolean>(false);
  const [showConfirmationModal, setShowConfirmationModal] = useState<boolean>(false);
  const [syncingUsers, setSyncingUsers] = useState<boolean>(false);

  useEffect(() => {
    store.cloudStore.updateItems(page);
    store.cloudStore.getCloudConnectionStatus().then((cloudStatus) => {
      setCloudIsConnected(cloudStatus.cloud_connection_status);
      setHeartbitStatus(cloudStatus.cloud_heartbeat_enabled);
      setHeartbitLink(cloudStatus.cloud_heartbeat_link);
    });
  }, []);

  const { count, results } = store.cloudStore.getSearchResult();

  const handleChangePage = (page: number) => {
    setPage(page);
    store.cloudStore.updateItems(page);
  };

  const handleChangeCloudApiKey = useCallback((e) => {
    setCloudApiKey(e.target.value);
    setApiKeyError(false);
  }, []);

  const saveKeyAndConnect = () => {
    setShowConfirmationModal(true);
  };

  const disconnectCloudOncall = () => {
    setCloudIsConnected(false);
    store.cloudStore.disconnectToCloud();
  };

  const connectToCloud = async () => {
    setShowConfirmationModal(false);
    const globalSettingItem = await store.globalSettingStore.getGlobalSettingItemByName('GRAFANA_CLOUD_ONCALL_TOKEN');
    store.globalSettingStore
      .update(globalSettingItem?.id, { name: 'GRAFANA_CLOUD_ONCALL_TOKEN', value: cloudApiKey })
      .then((response) => {
        if (response.error) {
          setCloudIsConnected(false);
          setApiKeyError(true);
          openErrorNotification(response.error);
        } else {
          setCloudIsConnected(true);
          syncUsers();
        }
      });
  };

  const syncUsers = async () => {
    setSyncingUsers(true);
    await store.cloudStore.syncCloudUsers();
    await store.cloudStore.updateItems();
    setSyncingUsers(false);
  };

  const handleLinkClick = (link: string) => {
    getLocationSrv().update({ partial: false, path: link });
  };

  const renderButtons = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
      case 0:
        return null;
      case 1:
        return null;
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
      case 3:
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
      default:
        return null;
    }
  };

  const renderStatus = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
      case 0:
        return <Text className={cx('error-message')}>Grafana Cloud is not synced</Text>;
      case 1:
        return <Text className={cx('error-message')}>User not found in Grafana Cloud</Text>;
      case 2:
        return <Text type="warning">Phone number is not verified in Grafana Cloud</Text>;
      case 3:
        return <Text type="success">Phone number verified</Text>;

      default:
        return <Text className={cx('error-message')}>User not found in Grafana Cloud</Text>;
    }
  };

  const renderStatusIcon = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
      case 0:
        return (
          <div className={cx('error-icon')}>
            <CrossCircleIcon />
          </div>
        );
      case 1:
        return (
          <div className={cx('error-icon')}>
            <CrossCircleIcon />
          </div>
        );

      case 2:
        return <Icon className={cx('warning-message')} name="exclamation-triangle" />;
      case 3:
        return <Icon className={cx('success-message')} name="check-circle" />;
      default:
        return (
          <div className={cx('error-message')}>
            <CrossCircleIcon />
          </div>
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

  const ConnectedBlock = (
    <VerticalGroup spacing="lg">
      <Block withBackground bordered className={cx('info-block')}>
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
      </Block>
      <Block bordered withBackground className={cx('info-block')}>
        <VerticalGroup>
          <Text.Title level={4}>
            <span className={cx('heart-icon')}>
              <HeartIcon />
            </span>
            Monitor cloud instance with heartbeat
          </Text.Title>
          <Text type="secondary">
            Once connected, current OnCall instance will send heartbeats every 3 minutes to the cloud Instance. If no
            heartbeat will be received in 10 minutes, cloud instance will issue an alert.
          </Text>
          {heartbitStatus && heartbitLink && (
            <Button
              variant="secondary"
              icon="external-link-alt"
              className={cx('block-button')}
              onClick={() => handleLinkClick(heartbitLink)}
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
              emptyText={results ? 'No variables found' : 'Loading...'}
              title={() => (
                <div className={cx('table-title')}>
                  <HorizontalGroup justify="space-between">
                    <Text type="secondary">
                      {count ? count : 0}
                      {` users matched between OSS and Cloud OnCall`}
                    </Text>
                    {syncingUsers ? (
                      <Button variant="primary" onClick={syncUsers} icon="sync" disabled>
                        Syncing...
                      </Button>
                    ) : (
                      <Button variant="primary" onClick={syncUsers} icon="sync">
                        Sync users
                      </Button>
                    )}
                  </HorizontalGroup>
                </div>
              )}
              rowKey="id"
              // @ts-ignore
              columns={columns}
              data={results}
              pagination={{
                page,
                total: Math.ceil((count || 0) / ITEMS_PER_PAGE),
                onChange: handleChangePage,
              }}
            />
          </div>
        </VerticalGroup>
      </Block>
    </VerticalGroup>
  );

  const DisconnectedBlock = (
    <VerticalGroup spacing="lg">
      <Block withBackground bordered className={cx('info-block')}>
        <VerticalGroup>
          <Text.Title level={4}>
            <Icon name="sync" className={cx('block-icon')} size="lg" /> Cloud OnCall API key
          </Text.Title>
          <Field
            label=""
            description="Find it in you Cloud OnCall -> Settings page"
            style={{ width: '100%' }}
            invalid={apiKeyError}
          >
            <Input id="cloudApiKey" onChange={handleChangeCloudApiKey} />
          </Field>
          <Button variant="primary" onClick={saveKeyAndConnect} disabled={!cloudApiKey} size="md">
            Save key and connect
          </Button>
        </VerticalGroup>
      </Block>
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
        </VerticalGroup>
      </Block>
      <Block bordered withBackground className={cx('info-block')}>
        <VerticalGroup>
          <Text.Title level={4}>
            <Icon name="bell" className={cx('block-icon')} size="lg" /> SMS and phone call notifications
          </Text.Title>

          <Text type="secondary">Users matched between OSS and Cloud OnCall currently unavialable.</Text>
        </VerticalGroup>
      </Block>
    </VerticalGroup>
  );

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="lg">
        <Text.Title level={3} className={cx('cloud-page-title')}>
          Connect Open Source OnCall and <Text className={cx('cloud-oncall-name')}>Cloud OnCall</Text>
        </Text.Title>
        {cloudIsConnected === undefined ? (
          <LoadingPlaceholder text="Loading..." />
        ) : cloudIsConnected ? (
          ConnectedBlock
        ) : (
          DisconnectedBlock
        )}

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
      </VerticalGroup>
    </div>
  );
});

export default withMobXProviderContext(CloudPage);
