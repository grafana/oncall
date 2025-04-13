import React, { useCallback, useEffect, useState } from 'react';

import { Alert, Button, Field, Icon, Input, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { determineRequiredAuthString, UserActions } from 'helpers/authorization/authorization';
import { PLUGIN_ROOT, StackSize } from 'helpers/consts';
import { openErrorNotification } from 'helpers/helpers';
import { PropsWithRouter, withRouter } from 'helpers/hoc';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { GTable } from 'components/GTable/GTable';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { CrossCircleIcon, HeartIcon } from 'icons/Icons';
import { Cloud } from 'models/cloud/cloud.types';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import { getCloudPageStyles } from './CloudPage.styles';

interface CloudPageProps extends WithStoreProps, PropsWithRouter<{}> {}
const ITEMS_PER_PAGE = 50;

const _CloudPage = observer((props: CloudPageProps) => {
  const store = useStore();
  const [page, setPage] = useState<number>(1);
  const styles = useStyles2(getCloudPageStyles);
  const [cloudApiKey, setCloudApiKey] = useState<string>('');
  const [apiKeyError, setApiKeyError] = useState<boolean>(false);
  const [cloudIsConnected, setCloudIsConnected] = useState<boolean>(undefined);
  const [cloudNotificationsEnabled, setCloudNotificationsEnabled] = useState<boolean>(false);
  const [heartbeatLink, setheartbeatLink] = useState<string>(null);
  const [heartbeatEnabled, setheartbeatEnabled] = useState<boolean>(false);
  const [_showConfirmationModal, setShowConfirmationModal] = useState<boolean>(false);
  const [syncingUsers, setSyncingUsers] = useState<boolean>(false);

  const {
    router: { navigate },
  } = props;

  useEffect(() => {
    (async () => {
      store.cloudStore.updateItems(page);
      const cloudStatus = await store.cloudStore.getCloudConnectionStatus();
      setCloudIsConnected(cloudStatus.cloud_connection_status);
      setheartbeatEnabled(cloudStatus.cloud_heartbeat_enabled);
      setheartbeatLink(cloudStatus.cloud_heartbeat_link);
      setCloudNotificationsEnabled(cloudStatus.cloud_notifications_enabled);
    })();
  }, [cloudIsConnected, page, store.cloudStore]);

  const { matched_users_count, results } = store.cloudStore.getSearchResult();

  const handleChangePage = (page: number) => {
    setPage(page);
    store.cloudStore.updateItems(page);
  };

  const handleChangeCloudApiKey = useCallback((e) => {
    setCloudApiKey(e.target.value);
    setApiKeyError(false);
  }, []);

  const disconnectCloudOncall = async () => {
    setCloudIsConnected(false);
    await store.cloudStore.disconnectToCloud();
    await store.cloudStore.loadCloudConnectionStatus();
  };

  const connectToCloud = async () => {
    setShowConfirmationModal(false);
    const globalSettingItem = await store.globalSettingStore.getGlobalSettingItemByName('GRAFANA_CLOUD_ONCALL_TOKEN');
    const response = await store.globalSettingStore.update(
      globalSettingItem?.id,
      { name: 'GRAFANA_CLOUD_ONCALL_TOKEN', value: cloudApiKey },
      { sync_users: false }
    );
    if (response.error) {
      setCloudIsConnected(false);
      setApiKeyError(true);
      openErrorNotification(response.error);
    } else {
      setCloudIsConnected(true);
      syncUsers();
      const heartbeatData: { link: string } = await store.cloudStore.getCloudHeartbeat();
      setheartbeatLink(heartbeatData?.link);
    }
    await store.cloudStore.loadCloudConnectionStatus();
  };

  const syncUsers = async () => {
    setSyncingUsers(true);
    await store.cloudStore.syncCloudUsers();
    await store.cloudStore.updateItems();
    setSyncingUsers(false);
  };

  const handleLinkClick = (link: string) => {
    window.open(link, '_blank');
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
            className={styles.tableButton}
            onClick={() => handleLinkClick(user?.cloud_data?.link)}
          >
            Open profile in Cloud
          </Button>
        );
      case 3:
        return (
          <Button
            variant="secondary"
            size="sm"
            className={styles.tableButton}
            onClick={() => navigate(`${PLUGIN_ROOT}/users/${user.id}`)}
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
        return <Text className={styles.errorMessage}>Grafana Cloud OnCall is not synced</Text>;
      case 1:
        return <Text className={styles.errorMessage}>User not found in Grafana Cloud OnCall</Text>;
      case 2:
        return <Text type="warning">Phone number is not verified in Grafana Cloud OnCall</Text>;
      case 3:
        return <Text type="success">Phone number verified</Text>;

      default:
        return <Text className={styles.errorMessage}>User not found in Grafana Cloud OnCall</Text>;
    }
  };

  const renderStatusIcon = (user: Cloud) => {
    switch (user?.cloud_data?.status) {
      case 0:
        return (
          <div className={styles.errorIcon}>
            <CrossCircleIcon />
          </div>
        );
      case 1:
        return (
          <div className={styles.errorIcon}>
            <CrossCircleIcon />
          </div>
        );

      case 2:
        return <Icon className={styles.warningMessage} name="exclamation-triangle" />;
      case 3:
        return <Icon className={styles.warningMessage} name="check-circle" />;
      default:
        return (
          <div className={styles.errorMessage}>
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
    <Stack direction="column" gap={StackSize.lg}>
      <Block withBackground bordered className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <Icon name="check" className={styles.infoBlock} size="lg" /> Grafana Cloud OnCall API key
          </Text.Title>
          <Text type="secondary">Grafana Cloud OnCall is sucessfully connected.</Text>

          <WithConfirm title="Are you sure to disconnect Cloud OnCall?" confirmText="Disconnect">
            <Button variant="destructive" onClick={disconnectCloudOncall} size="md" className={styles.blockButton}>
              Disconnect
            </Button>
          </WithConfirm>
        </Stack>
      </Block>
      <Block bordered withBackground className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <span className={styles.heartIcon}>
              <HeartIcon />
            </span>
            Monitor instance with heartbeat
          </Text.Title>
          <Text type="secondary">
            Once connected, current OnCall instance will send heartbeats every 3 minutes to the cloud Instance. If no
            heartbeat will be received in 10 minutes, cloud instance will issue an alert.
          </Text>
          <div className={styles.heartbeatButton}>
            {heartbeatEnabled ? (
              heartbeatLink ? (
                <Button
                  variant="secondary"
                  icon="external-link-alt"
                  className={styles.blockButton}
                  onClick={() => handleLinkClick(heartbeatLink)}
                >
                  Configure escalations in Cloud OnCall
                </Button>
              ) : (
                <Text type="secondary">Heartbeat will be created in a moment automatically</Text>
              )
            ) : (
              <Text type="secondary">Heartbeat is not enabled. You can go to the Env Variables tab and enable it</Text>
            )}
          </div>
        </Stack>
      </Block>
      <Block bordered withBackground className={styles.infoBlock}>
        {cloudNotificationsEnabled ? (
          <Stack direction="column">
            <Text.Title level={4}>
              <Icon name="bell" className={styles.blockIcon} size="lg" /> SMS and phone call notifications
            </Text.Title>

            <div style={{ width: '100%' }}>
              <Text type="secondary">
                {`Ask your users to sign up in Grafana Cloud OnCall, verify phone number and feel free to set up SMS & phone call notifications in personal settings! Users must have ${determineRequiredAuthString(
                  UserActions.NotificationsRead
                )} in order to be synced.`}
              </Text>

              <GTable
                className={styles.userTable}
                rowClassName={styles.userRow}
                showHeader={false}
                emptyText={results ? 'No variables found' : 'Loading...'}
                title={() => (
                  <div className={styles.tableTitle}>
                    <Stack justifyContent="space-between">
                      <Text type="secondary">
                        {matched_users_count ? matched_users_count : 0} user
                        {matched_users_count === 1 ? '' : 's'}
                        {` matched between OSS and Grafana Cloud OnCall`}
                      </Text>
                      <Button variant="primary" onClick={syncUsers} icon="sync" disabled={syncingUsers}>
                        {syncingUsers ? 'Syncing...' : 'Sync users'}
                      </Button>
                    </Stack>
                  </div>
                )}
                rowKey="id"
                // @ts-ignore
                columns={columns}
                data={results}
                pagination={{
                  page,
                  total: Math.ceil((matched_users_count || 0) / ITEMS_PER_PAGE),
                  onChange: handleChangePage,
                }}
              />
            </div>
          </Stack>
        ) : (
          <Stack direction="column">
            <Text.Title level={4}>
              <Icon name="bell" className={styles.blockIcon} size="lg" /> SMS and phone call notifications
            </Text.Title>
            <Text type="secondary">
              {'Please enable Grafana cloud notification to be able to see list of cloud users'}
            </Text>
          </Stack>
        )}
      </Block>
      <Block bordered withBackground className={styles.blockIcon}>
        <Stack direction="column">
          <Text.Title level={4}>
            <Icon name="mobile-android" className={styles.blockIcon} size="lg" /> Mobile app push notifications
          </Text.Title>
          <Text type="secondary">
            Connecting to Grafana Cloud OnCall enables sending push notifications on mobile devices using the Grafana
            OnCall mobile app.
          </Text>
        </Stack>
      </Block>
    </Stack>
  );

  const DisconnectedBlock = (
    <Stack direction="column" gap={StackSize.lg}>
      <Block withBackground bordered className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <Icon name="sync" className={styles.blockIcon} size="lg" /> Grafana Cloud OnCall API key
          </Text.Title>
          <Field
            label=""
            description="Find it on the Settings page of OnCall, within your Grafana Cloud OnCall instance"
            style={{ width: '100%' }}
            invalid={apiKeyError}
          >
            <Input id="cloudApiKey" onChange={handleChangeCloudApiKey} />
          </Field>
          <Button variant="primary" onClick={connectToCloud} disabled={!cloudApiKey} size="md">
            Save key and connect
          </Button>
        </Stack>
      </Block>
      <Block bordered withBackground className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <span className={styles.heartIcon}>
              <HeartIcon />
            </span>
            Monitor instance with heartbeat
          </Text.Title>
          <Text type="secondary">
            Once connected, this OnCall instance will send heartbeats every 3 minutes to the Grafana Cloud OnCall
            instance. If no heartbeats are received within 10 minutes, the Grafana Cloud OnCall instance will issue an
            alert.
          </Text>
        </Stack>
      </Block>
      <Block bordered withBackground className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <Icon name="bell" className={styles.blockIcon} size="lg" /> SMS and phone call notifications
          </Text.Title>

          <Text type="secondary">
            Connecting to Grafana Cloud OnCall enables sending SMS and phone call notifications using Grafana Cloud
            OnCall.
          </Text>
        </Stack>
      </Block>
      <Block bordered withBackground className={styles.infoBlock}>
        <Stack direction="column">
          <Text.Title level={4}>
            <Icon name="mobile-android" className={styles.blockIcon} size="lg" /> Mobile app push notifications
          </Text.Title>
          <Text type="secondary">
            Connecting to Grafana Cloud OnCall enables sending push notifications on mobile devices using the Grafana
            OnCall mobile app.
          </Text>
        </Stack>
      </Block>
    </Stack>
  );

  return (
    <Stack direction="column" gap={StackSize.lg}>
      <Alert severity="warning" title="">
        {
          <>
            As of March 24, 2026, Cloud Connection features for phone calls, SMS, and push notifications will no longer
            be supported in Grafana OnCall OSS.{' '}
            <a href={'https://grafana.com/docs/oncall/latest/set-up/open-source/'} target="_blank" rel="noreferrer">
              <Text type="link">
                <span>Learn more</span>
              </Text>
            </a>
          </>
        }
      </Alert>
      <Text.Title level={3}>
        Connect Open Source OnCall and <Text className={styles.cloudOncallName}>Grafana Cloud OnCall</Text>
      </Text.Title>
      {cloudIsConnected === undefined ? (
        <LoadingPlaceholder text="Loading..." />
      ) : cloudIsConnected ? (
        ConnectedBlock
      ) : (
        DisconnectedBlock
      )}
    </Stack>
  );
});

export const CloudPage = withRouter<{}, PropsWithRouter<{}>>(withMobXProviderContext(_CloudPage));
