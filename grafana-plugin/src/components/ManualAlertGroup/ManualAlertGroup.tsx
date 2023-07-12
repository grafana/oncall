import React, { FC, useCallback, useState } from 'react';

import {
  Alert,
  Button,
  Drawer,
  Field,
  HorizontalGroup,
  Icon,
  IconButton,
  IconName,
  Label,
  LoadingPlaceholder,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';

import GForm from 'components/GForm/GForm';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import EscalationVariants from 'containers/EscalationVariants/EscalationVariants';
import { prepareForUpdate } from 'containers/EscalationVariants/EscalationVariants.helpers';
import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import TeamName from 'containers/TeamName/TeamName';
import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import IntegrationHelper from 'pages/integration/Integration.helper';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils';

import { manualAlertFormConfig } from './ManualAlertGroup.config';

import styles from './ManualAlertGroup.module.css';

interface ManualAlertGroupProps {
  onHide: () => void;
  onCreate: (id: AlertType['pk']) => void;
  alertReceiveChannelStore: AlertReceiveChannelStore;
}

const cx = cn.bind(styles);

const ManualAlertGroup: FC<ManualAlertGroupProps> = (props) => {
  const store = useStore();
  const [userResponders, setUserResponders] = useState([]);
  const [scheduleResponders, setScheduleResponders] = useState([]);
  const { onHide, onCreate, alertReceiveChannelStore } = props;

  const [selectedTeamId, setSelectedTeam] = useState<GrafanaTeam['id']>();
  const [selectedTeamDirectPaging, setSelectedTeamDirectPaging] = useState<AlertReceiveChannel>();
  const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  const [chatOpsAvailableChannels, setChatopsAvailableChannels] = useState<any>();

  const data = {};

  const handleFormSubmit = async (data) => {
    if (selectedTeamId === undefined) {
      openWarningNotification('Select team first');
      return;
    }
    store.directPagingStore
      .createManualAlertRule(prepareForUpdate(userResponders, scheduleResponders, { team: selectedTeamId, ...data }))
      .then(({ alert_group_id: id }: { alert_group_id: AlertType['pk'] }) => {
        onCreate(id);
      })
      .finally(() => {
        onHide();
      });
  };

  const onUpdateSelectedTeam = async (selectedTeamId: GrafanaTeam['id']) => {
    setdirectPagingLoading(true);
    setSelectedTeamDirectPaging(null);
    setSelectedTeam(selectedTeamId);
    await alertReceiveChannelStore.updateItems({ team: selectedTeamId, integration: 'direct_paging' });
    const directPagingAlertReceiveChannel =
      alertReceiveChannelStore.getSearchResult() && alertReceiveChannelStore.getSearchResult()[0];
    if (directPagingAlertReceiveChannel) {
      setSelectedTeamDirectPaging(directPagingAlertReceiveChannel);
      await alertReceiveChannelStore.updateChannelFilters(directPagingAlertReceiveChannel.id);
      await store.slackChannelStore.updateItems();

      // Set unique available chatops channels
      const filterIds = alertReceiveChannelStore.channelFilterIds[directPagingAlertReceiveChannel.id];
      let availableChannels = [];
      let channelKeys = new Set();
      filterIds.map((channelFilterId) => {
        IntegrationHelper.getChatOpsChannels(alertReceiveChannelStore.channelFilters[channelFilterId], store)
          .filter((channel) => channel)
          .map((channel) => {
            if (!channelKeys.has(channel.name + channel.icon)) {
              availableChannels.push(channel);
              channelKeys.add(channel.name + channel.icon);
            }
          });
      });
      setChatopsAvailableChannels(Array.from(availableChannels));
    }
    setdirectPagingLoading(false);
  };

  const onUpdateEscalationVariants = useCallback(
    (value) => {
      setUserResponders(value.userResponders);
      setScheduleResponders(value.scheduleResponders);
    },
    [userResponders, scheduleResponders]
  );

  const DirectPagingIntegrationVariants = ({ selectedTeamId, selectedTeamDirectPaging, chatOpsAvailableChannels }) => {
    const renderWarningTitle = (
      <>
        <TeamName team={store.grafanaTeamStore.items[selectedTeamId]} />{' '}
        <Text>team doesn't have the the Direct Paging integration yet</Text>
      </>
    );

    const integrationDoesNotHaveEscalationChains = selectedTeamDirectPaging?.connected_escalations_chains_count === 0;

    return (
      <VerticalGroup>
        {selectedTeamId &&
          (directPagingLoading ? (
            <LoadingPlaceholder text="Loading..." />
          ) : selectedTeamDirectPaging ? (
            <VerticalGroup>
              <Label>Team will be notified according to the integration settings:</Label>
              <ul className={cx('responders-list')}>
                <li>
                  <HorizontalGroup justify="space-between">
                    <HorizontalGroup>
                      {integrationDoesNotHaveEscalationChains && (
                        <Tooltip content="Integration doesn't have connected escalation policies">
                          <Icon name="exclamation-triangle" style={{ color: 'var(--warning-text-color)' }} />
                        </Tooltip>
                      )}
                      <Text>{selectedTeamDirectPaging.verbal_name}</Text>
                    </HorizontalGroup>
                    <HorizontalGroup>
                      <Text type="secondary">Team:</Text>
                      <TeamName team={store.grafanaTeamStore.items[selectedTeamId]} />
                    </HorizontalGroup>
                    <HorizontalGroup>
                      {chatOpsAvailableChannels && (
                        <>
                          <Text type="secondary">ChatOps:</Text>{' '}
                          {chatOpsAvailableChannels.map(
                            (chatOpsChannel: { name: string; icon: IconName }, chatOpsIndex) => (
                              <div
                                key={`${chatOpsChannel?.name}-${chatOpsIndex}`}
                                className={cx({
                                  'u-margin-right-xs': chatOpsIndex !== chatOpsAvailableChannels.length,
                                })}
                              >
                                {chatOpsChannel?.icon && <Icon name={chatOpsChannel.icon} className={cx('icon')} />}
                                <Text type="primary">{chatOpsChannel?.name || ''}</Text>
                              </div>
                            )
                          )}
                        </>
                      )}
                    </HorizontalGroup>
                    <HorizontalGroup>
                      <PluginLink target="_blank" query={{ page: 'integrations', id: selectedTeamDirectPaging.id }}>
                        <IconButton
                          tooltip="Open integration in new tab"
                          style={{ color: 'var(--always-gray)' }}
                          name="external-link-alt"
                        />
                      </PluginLink>
                    </HorizontalGroup>
                  </HorizontalGroup>
                </li>
              </ul>

              {(integrationDoesNotHaveEscalationChains || !chatOpsAvailableChannels) && (
                <Alert severity="warning" title="Possible notification miss">
                  <VerticalGroup>
                    {integrationDoesNotHaveEscalationChains && (
                      <Text>
                        Integration doesn't have connected escalation policies. Consider adding responders manually by
                        user or by email
                      </Text>
                    )}
                    {!chatOpsAvailableChannels && (
                      <Text>Integration doesn't have connected ChatOps channels in messengers.</Text>
                    )}
                  </VerticalGroup>
                </Alert>
              )}
            </VerticalGroup>
          ) : (
            <Alert severity="warning" title={renderWarningTitle}>
              <VerticalGroup>
                <Text>
                  Empty integration for this team will be created automatically. Consider selecting responders by
                  schedule or user below
                </Text>
              </VerticalGroup>
            </Alert>
          ))}
      </VerticalGroup>
    );
  };

  const submitButtonDisabled = !(
    selectedTeamId &&
    (selectedTeamDirectPaging || userResponders.length || scheduleResponders.length)
  );

  return (
    <Drawer
      scrollableContent
      title="Create manual alert group (Direct Paging)"
      onClose={onHide}
      closeOnMaskClick={false}
      width="70%"
    >
      <VerticalGroup>
        <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
        <Field label="Select team you want to notify">
          <GrafanaTeamSelect withoutModal onSelect={onUpdateSelectedTeam} />
        </Field>
        <DirectPagingIntegrationVariants
          selectedTeamId={selectedTeamId}
          selectedTeamDirectPaging={selectedTeamDirectPaging}
          chatOpsAvailableChannels={chatOpsAvailableChannels}
        />
        <EscalationVariants
          value={{ userResponders, scheduleResponders }}
          onUpdateEscalationVariants={onUpdateEscalationVariants}
          variant={'secondary'}
          withLabels={true}
        />
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button type="submit" form={manualAlertFormConfig.name} disabled={submitButtonDisabled}>
            Create
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Drawer>
  );
};

export default ManualAlertGroup;
