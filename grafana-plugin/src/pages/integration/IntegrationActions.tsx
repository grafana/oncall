import React, { useEffect, useState } from 'react';

import { Button, ConfirmModal, Icon, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { INTEGRATION_SERVICENOW, StackSize, GENERIC_ERROR, PLUGIN_ROOT } from 'helpers/consts';
import { openErrorNotification, openNotification } from 'helpers/helpers';
import { useDrawer } from 'helpers/hooks';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { useNavigate } from 'react-router-dom-v5-compat';

import { HamburgerContextMenu } from 'components/HamburgerContextMenu/HamburgerContextMenu';
import { IntegrationSendDemoAlertModal } from 'components/IntegrationSendDemoAlertModal/IntegrationSendDemoAlertModal';
import { Text } from 'components/Text/Text';
import { IntegrationHeartbeatForm } from 'containers/IntegrationContainers/IntegrationHeartbeatForm/IntegrationHeartbeatForm';
import { IntegrationFormContainer } from 'containers/IntegrationForm/IntegrationFormContainer';
import { IntegrationLabelsForm } from 'containers/IntegrationLabelsForm/IntegrationLabelsForm';
import { MaintenanceForm } from 'containers/MaintenanceForm/MaintenanceForm';
import { CompleteServiceNowModal } from 'containers/ServiceNowConfigDrawer/CompleteServiceNowConfigModal';
import { ServiceNowConfigDrawer } from 'containers/ServiceNowConfigDrawer/ServiceNowConfigDrawer';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import { IntegrationDrawerKey } from './Integration';
import { getIsBidirectionalIntegration } from './Integration.helper';
import { getIntegrationStyles } from './Integration.styles';

interface IntegrationActionsProps {
  isLegacyIntegration: boolean;
  alertReceiveChannel: ApiSchemas['AlertReceiveChannel'];
  changeIsTemplateSettingsOpen: () => void;
  drawerConfig: ReturnType<typeof useDrawer<IntegrationDrawerKey>>;
}

export const IntegrationActions: React.FC<IntegrationActionsProps> = ({
  alertReceiveChannel,
  isLegacyIntegration,
  changeIsTemplateSettingsOpen,
  drawerConfig,
}) => {
  const store = useStore();
  const navigate = useNavigate();

  const { alertReceiveChannelStore } = store;

  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: any;
    dismissText: string;
    confirmText: string;
    body?: React.ReactNode;
    description?: string;
    confirmationText?: string;
    onConfirm: () => void;
  }>(undefined);

  const [isCompleteServiceNowConfigOpen, setIsCompleteServiceNowConfigOpen] = useState(false);
  const [isIntegrationSettingsOpen, setIsIntegrationSettingsOpen] = useState(false);
  const [isLabelsFormOpen, setLabelsFormOpen] = useState(false);
  const [isHeartbeatFormOpen, setIsHeartbeatFormOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [maintenanceData, setMaintenanceData] = useState<{
    alert_receive_channel_id: ApiSchemas['AlertReceiveChannel']['id'];
  }>(undefined);

  const styles = useStyles2(getIntegrationStyles);

  const { closeDrawer, openDrawer, getIsDrawerOpened } = drawerConfig;

  const { id } = alertReceiveChannel;

  useEffect(() => {
    /* ServiceNow Only */
    openServiceNowCompleteConfigurationDrawer();
  }, []);

  return (
    <>
      {confirmModal && (
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          title={confirmModal.title}
          confirmText={confirmModal.confirmText}
          dismissText="Cancel"
          body={confirmModal.body}
          description={confirmModal.description}
          confirmationText={confirmModal.confirmationText}
          onConfirm={confirmModal.onConfirm}
          onDismiss={() => setConfirmModal(undefined)}
        />
      )}

      {alertReceiveChannel.demo_alert_enabled && (
        <IntegrationSendDemoAlertModal
          alertReceiveChannel={alertReceiveChannel}
          isOpen={isDemoModalOpen}
          onHideOrCancel={() => setIsDemoModalOpen(false)}
        />
      )}

      {getIsDrawerOpened(INTEGRATION_SERVICENOW) && <ServiceNowConfigDrawer onHide={closeDrawer} />}

      {isCompleteServiceNowConfigOpen && (
        <CompleteServiceNowModal onHide={() => setIsCompleteServiceNowConfigOpen(false)} />
      )}

      {isIntegrationSettingsOpen && (
        <IntegrationFormContainer
          isTableView={false}
          onHide={() => setIsIntegrationSettingsOpen(false)}
          onSubmit={async () => {
            await alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id);
          }}
          id={alertReceiveChannel['id']}
          navigateToAlertGroupLabels={(_id: ApiSchemas['AlertReceiveChannel']['id']) => {
            setIsIntegrationSettingsOpen(false);
            setLabelsFormOpen(true);
          }}
        />
      )}

      {isLabelsFormOpen && (
        <IntegrationLabelsForm
          onHide={() => {
            setLabelsFormOpen(false);
          }}
          onSubmit={() => alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id)}
          id={alertReceiveChannel['id']}
          onOpenIntegrationSettings={() => {
            setIsIntegrationSettingsOpen(true);
          }}
        />
      )}

      {isHeartbeatFormOpen && (
        <IntegrationHeartbeatForm
          alertReceveChannelId={alertReceiveChannel['id']}
          onClose={() => setIsHeartbeatFormOpen(false)}
        />
      )}

      {maintenanceData && (
        <MaintenanceForm
          initialData={maintenanceData}
          onUpdate={() => alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id)}
          onHide={() => setMaintenanceData(undefined)}
        />
      )}

      <div className={styles.integrationActions}>
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsTest}>
          <Button
            variant="secondary"
            size="md"
            onClick={() => setIsDemoModalOpen(true)}
            data-testid="send-demo-alert"
            disabled={!alertReceiveChannel.demo_alert_enabled}
            tooltip={alertReceiveChannel.demo_alert_enabled ? '' : 'Demo Alerts are not enabled for this integration'}
          >
            Send demo alert
          </Button>
        </WithPermissionControlTooltip>

        <div data-testid="integration-settings-context-menu-wrapper">
          <HamburgerContextMenu
            items={[
              {
                onClick: openIntegrationSettings,
                label: 'Integration Settings',
              },
              {
                label: 'ServiceNow configuration',
                hidden: !getIsBidirectionalIntegration(alertReceiveChannel),
                onClick: () => openDrawer(INTEGRATION_SERVICENOW),
              },
              {
                onClick: openLabelsForm,
                hidden: !store.hasFeature(AppFeature.Labels),
                label: 'Alert group labeling',
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                onClick: () => setIsHeartbeatFormOpen(true),
                hidden: !showHeartbeatSettings(),
                label: <div data-testid="integration-heartbeat-settings">Heartbeat Settings</div>,
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                onClick: openStartMaintenance,
                hidden: Boolean(alertReceiveChannel.maintenance_till),
                label: 'Start Maintenance',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: changeIsTemplateSettingsOpen,
                label: 'Edit Templates',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: () => {
                  setConfirmModal({
                    isOpen: true,
                    confirmText: 'Stop',
                    dismissText: 'Cancel',
                    onConfirm: onStopMaintenance,
                    title: 'Stop Maintenance',
                    body: (
                      <Text type="primary">
                        Are you sure you want to stop the maintenance for{' '}
                        <Emoji text={alertReceiveChannel.verbal_name} /> ?
                      </Text>
                    ),
                  });
                },
                hidden: !alertReceiveChannel.maintenance_till,
                label: 'Stop Maintenance',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: () =>
                  setConfirmModal({
                    isOpen: true,
                    title: 'Migrate Integration?',
                    body: (
                      <Stack direction="column" gap={StackSize.lg}>
                        <Text type="primary">
                          Are you sure you want to migrate <Emoji text={alertReceiveChannel.verbal_name} /> ?
                        </Text>

                        <Stack direction="column" gap={StackSize.xs}>
                          <Text type="secondary">- Integration internal behaviour will be changed</Text>
                          <Text type="secondary">
                            - Integration URL will stay the same, so no need to change {getMigrationDisplayName()}{' '}
                            configuration
                          </Text>
                          <Text type="secondary">- Integration templates will be reset to suit the new payload</Text>
                          <Text type="secondary">- It is needed to adjust routes manually to the new payload</Text>
                        </Stack>
                      </Stack>
                    ),
                    onConfirm: onIntegrationMigrate,
                    dismissText: 'Cancel',
                    confirmText: 'Migrate',
                  }),
                hidden: !isLegacyIntegration,
                label: 'Migrate',
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                label: (
                  <CopyToClipboard
                    text={alertReceiveChannel.id}
                    onCopy={() => openNotification('Integration ID is copied')}
                  >
                    <div>
                      <Stack gap={StackSize.xs}>
                        <Icon name="copy" />
                        <Text type="primary">UID: {alertReceiveChannel.id}</Text>
                      </Stack>
                    </div>
                  </CopyToClipboard>
                ),
              },
              {
                onClick: () => {
                  setConfirmModal({
                    isOpen: true,
                    title: 'Delete Integration?',
                    body: (
                      <Text type="primary">
                        Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} /> ?
                      </Text>
                    ),
                    onConfirm: deleteIntegration,
                    dismissText: 'Cancel',
                    confirmText: 'Delete',
                  });
                },
                hidden: !alertReceiveChannel.allow_delete,
                label: (
                  <Text type="danger">
                    <Stack gap={StackSize.xs}>
                      <Icon name="trash-alt" />
                      <span>Delete Integration</span>
                    </Stack>
                  </Text>
                ),
                requiredPermission: UserActions.IntegrationsWrite,
              },
            ]}
          />
        </div>
      </div>
    </>
  );

  function openServiceNowCompleteConfigurationDrawer() {
    const isServiceNow = getIsBidirectionalIntegration(alertReceiveChannel);
    const isConfigured = alertReceiveChannel.additional_settings?.is_configured;
    if (isServiceNow && !isConfigured) {
      setIsCompleteServiceNowConfigOpen(true);
    }
  }

  function getMigrationDisplayName() {
    const name = alertReceiveChannel.integration.toLowerCase().replace('legacy_', '');
    switch (name) {
      case 'grafana_alerting':
        return 'Grafana Alerting';
      case 'alertmanager':
      default:
        return 'AlertManager';
    }
  }

  async function onIntegrationMigrate() {
    try {
      await AlertReceiveChannelHelper.migrateChannel(alertReceiveChannel.id);
      setConfirmModal(undefined);
      openNotification('Integration has been successfully migrated.');
      await Promise.all([
        alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id),
        alertReceiveChannelStore.fetchTemplates(alertReceiveChannel.id),
      ]);
    } catch (_err) {
      openErrorNotification(GENERIC_ERROR);
    }
  }

  function showHeartbeatSettings() {
    return alertReceiveChannel.is_available_for_integration_heartbeat;
  }

  async function deleteIntegration() {
    try {
      await AlertReceiveChannelHelper.deleteAlertReceiveChannel(alertReceiveChannel.id);
      navigate(`${PLUGIN_ROOT}/integrations`);
      openNotification('Integration has been succesfully deleted.');
    } catch (_err) {
      openErrorNotification(GENERIC_ERROR);
    }
  }

  function openIntegrationSettings() {
    setIsIntegrationSettingsOpen(true);
  }

  function openLabelsForm() {
    setLabelsFormOpen(true);
  }

  function openStartMaintenance() {
    setMaintenanceData({ alert_receive_channel_id: alertReceiveChannel.id });
  }

  async function onStopMaintenance() {
    setConfirmModal(undefined);

    await AlertReceiveChannelHelper.stopMaintenanceMode(id);

    openNotification('Maintenance has been stopped');
    await alertReceiveChannelStore.fetchItemById(id);
  }
};
