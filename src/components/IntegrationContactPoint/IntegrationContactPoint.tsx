import React, { useEffect, useReducer } from 'react';

import { css, cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import {
  Button,
  Drawer,
  Icon,
  IconButton,
  Input,
  RadioButtonGroup,
  Select,
  Tooltip,
  Stack,
  useStyles2,
} from '@grafana/ui';
import { StackSize, GENERIC_ERROR } from 'helpers/consts';
import { openNotification, openErrorNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';

import { GTable } from 'components/GTable/GTable';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ContactPoint } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getIntegrationStyles } from 'pages/integration/Integration.styles';
import { useStore } from 'state/useStore';

interface IntegrationContactPointState {
  isLoading: boolean;
  isDrawerOpen: boolean;
  isConnectOpen: boolean;
  isExistingContactPoint: boolean;
  allContactPoints: Array<{ name: string; uid: string; contact_points: string[] }>;

  // dropdown selected values
  selectedAlertManager: string;
  selectedContactPoint: string;

  // dropdown options
  dataSourceOptions: Array<{ label: string; value: string }>;
  contactPointOptions: Array<{ label: string; value: string }>;
}

export const IntegrationContactPoint: React.FC<{
  id: ApiSchemas['AlertReceiveChannel']['id'];
}> = observer(({ id }) => {
  const styles = useStyles2(getIntegrationStyles);
  const { alertReceiveChannelStore } = useStore();
  const contactPoints = alertReceiveChannelStore.connectedContactPoints[id];
  const warnings = contactPoints?.filter((cp) => !cp.notificationConnected);
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
      isExistingContactPoint,
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
      isExistingContactPoint: true,
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
      const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();
      setState({
        allContactPoints: response,
        dataSourceOptions: response.map((res) => ({ label: res.name, value: res.uid })),
      });
    })();
  }, []);

  const radioOptions = [
    {
      label: 'Connect existing Contact point',
      value: 'existing',
    },
    {
      label: 'Create a new one',
      value: 'new',
    },
  ];

  return (
    <IntegrationBlock
      noContent={true}
      heading={
        <div
          className={css`
            display: flex;
            justify-content: space-between;
          `}
        >
          {isDrawerOpen && (
            <Drawer scrollableContent title="Connected Contact Points" onClose={closeDrawer} closeOnMaskClick={false}>
              <div>
                <GTable
                  emptyText={'No contact points'}
                  className={styles.contactPointsTable}
                  rowKey="id"
                  data={contactPoints}
                  columns={getTableColumns()}
                />

                <div className={styles.contactPointsConnect}>
                  <Stack direction="column" gap={StackSize.md}>
                    <div
                      className={styles.contactPointsConnectToggler}
                      onClick={() => setState({ isConnectOpen: !isConnectOpen })}
                    >
                      <Stack justifyContent="space-between">
                        <Stack gap={StackSize.xs} alignItems="center">
                          <Text type="primary">Grafana Alerting Contact point</Text>
                          <Icon name="info-circle" />
                        </Stack>

                        {isConnectOpen ? <Icon name="arrow-down" /> : <Icon name="arrow-right" />}
                      </Stack>
                    </div>

                    {renderConnectSection()}
                  </Stack>
                </div>
              </div>
            </Drawer>
          )}

          <Stack gap={StackSize.md}>
            <IntegrationTag>Contact point</IntegrationTag>

            {contactPoints?.length ? (
              <Stack>
                <Text type="primary">
                  {contactPoints.length} contact point{contactPoints.length === 1 ? '' : 's'} connected
                </Text>
                {warnings.length > 0 && (
                  <Tooltip
                    content={'Check the notification policy for the contact point in Grafana Alerting'}
                    placement={'top'}
                  >
                    <div
                      className={css`
                        display: flex;
                        gap: 4px;
                      `}
                    >
                      {renderExclamationIcon()}
                      <Text type="primary">{warnings.length} with error</Text>
                    </div>
                  </Tooltip>
                )}
              </Stack>
            ) : (
              <Stack gap={StackSize.xs}>
                {renderExclamationIcon()}
                <Text type="primary" data-testid="integration-escalation-chain-not-selected">
                  Connect Alerting Contact point to receive alerts
                </Text>
              </Stack>
            )}
          </Stack>

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

  function renderConnectSection() {
    if (!isConnectOpen) {
      return null;
    }

    return (
      <Stack direction="column" gap={StackSize.md}>
        <RadioButtonGroup
          options={radioOptions}
          value={isExistingContactPoint ? 'existing' : 'new'}
          onChange={(radioValue) => {
            setState({
              isExistingContactPoint: radioValue === 'existing',
              contactPointOptions: [],
              selectedAlertManager: null,
              selectedContactPoint: null,
            });
          }}
        />

        <Select
          options={dataSourceOptions}
          onChange={onAlertManagerChange}
          value={selectedAlertManager}
          placeholder="Select Alert Manager"
        />

        {isExistingContactPoint ? (
          <Select
            options={contactPointOptions}
            onChange={onContactPointChange}
            value={selectedContactPoint}
            placeholder="Select Contact Point"
          />
        ) : (
          <Input
            value={selectedContactPoint}
            placeholder="Enter New Contact Point Name"
            onChange={({ target }) => {
              const value = (target as HTMLInputElement).value;
              setState({ selectedContactPoint: value });
            }}
          />
        )}

        <Stack alignItems="center">
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
          {isLoading && (
            <Icon
              name="fa fa-spinner"
              size="md"
              className={css`
                margin-bottom: 0;
                margin-right: 4px;
              `}
            />
          )}
        </Stack>
      </Stack>
    );
  }

  function renderActions(item: ContactPoint) {
    const onDisconnect = async () => {
      try {
        await AlertReceiveChannelHelper.disconnectContactPoint(id, item.dataSourceId, item.contactPoint);
        closeDrawer();
        openNotification('Contact point has been removed');
        alertReceiveChannelStore.fetchConnectedContactPoints(id);
      } catch (_err) {
        openErrorNotification(GENERIC_ERROR);
      }
    };

    return (
      <Stack gap={StackSize.md}>
        <IconButton
          aria-label="Alert Manager"
          name="external-link-alt"
          onClick={() => {
            window.open(
              `${window.location.origin}/alerting/notifications/receivers/${item.contactPoint}/edit?alertmanager=${item.dataSourceId}`,
              '_blank'
            );
          }}
        />
        <WithConfirm
          title={`Disconnect Contact point`}
          confirmText="Disconnect"
          description={
            <Stack direction="column" gap={StackSize.md}>
              <Text type="primary">
                When the contact point will be disconnected, the Integration will no longer receive alerts for it.
              </Text>
              <Text type="primary">You can add new contact point at any time.</Text>
            </Stack>
          }
        >
          <IconButton aria-label="Disconnect Contact Point" name="trash-alt" onClick={onDisconnect} />
        </WithConfirm>
      </Stack>
    );
  }

  function renderContactPointName(item: ContactPoint) {
    return (
      <Stack gap={StackSize.xs}>
        <Text type="primary">{item.contactPoint}</Text>

        {!item.notificationConnected && (
          <Tooltip
            content={'Check the notification policy for this contact point in Grafana Alerting'}
            placement={'top'}
          >
            {renderExclamationIcon()}
          </Tooltip>
        )}
      </Stack>
    );
  }

  function renderAlertManager(item: ContactPoint) {
    return item.dataSourceName;
  }

  function renderExclamationIcon() {
    return (
      <div className={cx(styles.iconExclamation)}>
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

  async function onContactPointConnect() {
    setState({ isLoading: true });
    try {
      await (isExistingContactPoint
        ? AlertReceiveChannelHelper.connectContactPoint(id, selectedAlertManager, selectedContactPoint)
        : AlertReceiveChannelHelper.createContactPoint(id, selectedAlertManager, selectedContactPoint));
      closeDrawer();
      openNotification('A new contact point has been connected to your integration');
      alertReceiveChannelStore.fetchConnectedContactPoints(id);
    } catch (ex) {
      const error = ex.response?.data?.detail ?? GENERIC_ERROR;
      openErrorNotification(error);
    } finally {
      setState({ isLoading: false });
    }
  }

  function onAlertManagerChange(option: SelectableValue<string>) {
    setState({
      selectedAlertManager: option.value,
      selectedContactPoint: null,
      contactPointOptions: allContactPoints
        .find((opt) => opt.uid === option.value)
        ?.contact_points.map((cp) => ({ value: cp, label: cp })),
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
