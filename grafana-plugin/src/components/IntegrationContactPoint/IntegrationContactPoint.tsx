import { Button, Drawer, HorizontalGroup, Icon, IconButton, Select, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import { observer } from 'mobx-react';
import { AlertReceiveChannel, ContactPoint } from 'models/alert_receive_channel/alert_receive_channel.types';
import React, { useEffect, useReducer } from 'react';
import { useStore } from 'state/useStore';

import Tag from 'components/Tag/Tag';
import styles from 'pages/integration/Integration.module.scss';
import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import { getVar } from 'utils/DOM';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { openErrorNotification, openNotification } from 'utils';
import { SelectableValue } from '@grafana/data';

const cx = cn.bind(styles);

interface IntegrationContactPointState {
  isLoading: boolean;
  isDrawerOpen: boolean;
  isConnectOpen: boolean;
  allContactPoints: Array<{ name: string; uid: string; contact_points: string[] }>;

  // dropdown selected values
  selectedAlertManager: string;
  selectedContactPoint: string;

  // dropdown options
  dataSourceOptions: Array<{ label: string; value: string }>;
  contactPointOptions: Array<{ label: string; value: string }>;
}

const IntegrationContactPoint: React.FC<{
  id: AlertReceiveChannel['id'];
}> = observer(({ id }) => {
  const { alertReceiveChannelStore } = useStore();
  const contactPoints = alertReceiveChannelStore.connectedContactPoints[id];
  const warnings = contactPoints.filter((cp) => !cp.notificationConnected);

  const [
    {
      isLoading,
      isDrawerOpen,
      allContactPoints,
      dataSourceOptions,
      contactPointOptions,
      selectedAlertManager,
      selectedContactPoint,
      isConnectOpen,
    },
    setState,
  ] = useReducer(
    (state: IntegrationContactPointState, newState: Partial<IntegrationContactPointState>) => ({
      ...state,
      ...newState,
    }),
    {
      isLoading: false,
      isDrawerOpen: false,
      contactPointOptions: [],
      dataSourceOptions: [],
      allContactPoints: [],
      selectedAlertManager: undefined,
      selectedContactPoint: undefined,
      isConnectOpen: false,
    }
  );

  useEffect(() => {
    (async function () {
      const response = await alertReceiveChannelStore.getGrafanaAlertingContactPoints();
      setState({
        allContactPoints: response,
        dataSourceOptions: response.map((res) => ({ label: res.name, value: res.uid })),
      });
    })();
  }, []);

  return (
    <IntegrationBlock
      noContent={true}
      heading={
        <div className={cx('u-flex', 'u-flex-space-between')}>
          {isDrawerOpen && (
            <Drawer scrollableContent title="Contact Points" onClose={closeDrawer} closeOnMaskClick={false}>
              <div className={cx('contactpoints__drawer')}>
                <GTable
                  className={cx('contactpoints__table')}
                  rowKey="id"
                  data={contactPoints}
                  columns={getTableColumns()}
                />

                <div className={cx('contactpoints__connect')}>
                  <VerticalGroup spacing="md">
                    <div
                      className={cx('contactpoints__connect-toggler')}
                      onClick={() => setState({ isConnectOpen: !isConnectOpen })}
                    >
                      <HorizontalGroup spacing="xs">
                        <Text type="primary">Connect existing contact point</Text>
                        {isConnectOpen ? <Icon name="arrow-down" /> : <Icon name="arrow-right" />}
                      </HorizontalGroup>
                    </div>

                    {isConnectOpen && (
                      <VerticalGroup spacing="md">
                        <Select
                          options={dataSourceOptions}
                          onChange={onAlertManagerChange}
                          value={selectedAlertManager}
                          placeholder="Select Alert Manager"
                        />

                        <Select
                          options={contactPointOptions}
                          onChange={onContactPointChange}
                          value={selectedContactPoint}
                          placeholder="Select Contact Point"
                        />

                        <HorizontalGroup align="center">
                          <Button
                            variant="primary"
                            disabled={!selectedAlertManager || !selectedContactPoint || isLoading}
                            onClick={onContactPointConnect}
                          >
                            Connect contact point
                          </Button>
                          <Button variant="secondary" onClick={closeDrawer}>
                            Cancel
                          </Button>
                          {isLoading && <Icon name="fa fa-spinner" size="md" className={cx('loadingPlaceholder')} />}
                        </HorizontalGroup>
                      </VerticalGroup>
                    )}
                  </VerticalGroup>
                </div>
              </div>
            </Drawer>
          )}

          <HorizontalGroup spacing="md">
            <Tag color={getVar('--tag-secondary-transparent')} border={getVar('--border-weak')} className={cx('tag')}>
              <Text type="primary" size="small" className={cx('radius')}>
                Contact point
              </Text>
            </Tag>

            {contactPoints?.length ? (
              <HorizontalGroup>
                <Text type="primary">
                  {contactPoints.length} contact point{contactPoints.length === 1 ? '' : 's'} connected
                </Text>
                {warnings.length > 0 && (
                  <HorizontalGroup spacing="xs">
                    {renderExclamationIcon()}
                    <Text type="primary">{warnings.length} with error</Text>
                  </HorizontalGroup>
                )}
              </HorizontalGroup>
            ) : (
              <HorizontalGroup spacing="xs">
                {renderExclamationIcon()}
                <Text type="primary" data-testid="integration-escalation-chain-not-selected">
                  Connect Alerting Contact point to receive alerts
                </Text>
              </HorizontalGroup>
            )}
          </HorizontalGroup>

          <Button
            variant={'secondary'}
            icon="edit"
            size={'sm'}
            tooltip="Edit"
            id={'openContactPoint'}
            onClick={() => setState({ isDrawerOpen: true })}
          />
        </div>
      }
      content={undefined}
    />
  );

  function renderActions(item: ContactPoint) {
    return (
      <HorizontalGroup spacing="md">
        <IconButton
          name="external-link-alt"
          onClick={() => {
            window.open(
              `${window.location.host}/alerting/notifications/receivers/${item.contactPoint}/edit?alertmanager=${item.dataSourceId}`,
              '_blank'
            );
          }}
        />
        <WithConfirm
          title={`Disconnect Contact point`}
          confirmText="Disconnect"
          description={
            <VerticalGroup spacing="md">
              <Text type="primary">
                When the contact point will be disconnected, the Integration will no longer receive alerts for it.
              </Text>
              <Text type="primary">You can add new contact point at any time.</Text>
            </VerticalGroup>
          }
        >
          <IconButton
            name="trash-alt"
            onClick={() => {
              alertReceiveChannelStore
                .disconnectContactPoint(id, item.dataSourceId, item.contactPoint)
                .then(() => {
                  closeDrawer();
                  openNotification('Contact point has been removed');
                  alertReceiveChannelStore.updateConnectedContactPoints(id);
                })
                .catch(() => openErrorNotification('An error has occurred. Please try again.'));
            }}
          />
        </WithConfirm>
      </HorizontalGroup>
    );
  }

  function renderContactPointName(item: ContactPoint) {
    return (
      <HorizontalGroup spacing="xs">
        <Text type="primary">{item.contactPoint}</Text>

        {!item.notificationConnected && (
          <div className={cx('icon-exclamation')}>
            <Icon name="exclamation-triangle" />
          </div>
        )}
      </HorizontalGroup>
    );
  }

  function renderAlertManager(item: ContactPoint) {
    return item.dataSourceName;
  }

  function renderExclamationIcon() {
    return (
      <div className={cx('icon-exclamation')}>
        <Icon name="exclamation-triangle" />
      </div>
    );
  }

  function closeDrawer() {
    setState({
      isDrawerOpen: false,
      isConnectOpen: false,
      selectedAlertManager: undefined,
      selectedContactPoint: undefined,
    });
  }

  function onContactPointConnect() {
    setState({ isLoading: true });
    alertReceiveChannelStore
      .connectContactPoint(id, selectedAlertManager, selectedContactPoint)
      .then(() => {
        closeDrawer();
        openNotification('A new contact point has been connected to your integration');
        alertReceiveChannelStore.updateConnectedContactPoints(id);
      })
      .catch(() => {
        openErrorNotification('An error has occurred. Please try again.');
      })
      .finally(() => setState({ isLoading: false }));
  }

  function onAlertManagerChange(option: SelectableValue<string>) {
    const currentContactPoints = contactPoints
      .filter((p) => p.dataSourceId === option.value)
      .map((p) => p.contactPoint);

    setState({
      selectedAlertManager: option.value,
      selectedContactPoint: undefined,
      contactPointOptions: allContactPoints
        .find((opt) => opt.uid == option.value)
        .contact_points?.filter((cp) => currentContactPoints.indexOf(cp) === -1)
        .map((cp) => ({ value: cp, label: cp })),
    });
  }

  function onContactPointChange(option: SelectableValue<string>) {
    setState({ selectedContactPoint: option.value });
  }

  function getTableColumns(): Array<{ width: string; key: string; title?: string; render }> {
    return [
      {
        width: '40%',
        key: 'name',
        title: 'Name',
        render: renderContactPointName,
      },
      {
        width: '40%',
        title: 'Alert Manager',
        key: 'alertmanager',
        render: renderAlertManager,
      },
      {
        width: '20%',
        title: '',
        key: 'actions',
        render: renderActions,
      },
    ];
  }
});

export default IntegrationContactPoint;
