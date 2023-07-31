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

      // The code below is used to get the unique available chotops channels for all routes in integraion
      // This is the workaround for IntegrationHelper.getChatOpsChannels, it should be moved to the helper
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
    const escalationChainsExist = selectedTeamDirectPaging?.connected_escalations_chains_count !== 0;

    return (
      <VerticalGroup>
        {selectedTeamId &&
          (directPagingLoading ? (
            <LoadingPlaceholder text="Loading..." />
          ) : selectedTeamDirectPaging ? (
            <VerticalGroup>
              <Label>Integration to be used for notification</Label>
              <ul className={cx('responders-list')}>
                <li>
                  <HorizontalGroup justify="space-between">
                    <HorizontalGroup>
                      <Text>{selectedTeamDirectPaging.verbal_name}</Text>
                    </HorizontalGroup>
                    <HorizontalGroup>
                      <Text type="secondary">Team:</Text>
                      <TeamName team={store.grafanaTeamStore.items[selectedTeamId]} />
                    </HorizontalGroup>
                    {chatOpsAvailableChannels.length && (
                      <HorizontalGroup>
                        {chatOpsAvailableChannels.map(
                          (chatOpsChannel: { name: string; icon: IconName }, chatOpsIndex) => (
                            <div key={`${chatOpsChannel.name}-${chatOpsIndex}`}>
                              {chatOpsChannel.icon && <Icon name={chatOpsChannel.icon} />}
                              <Text type="primary">{chatOpsChannel.name || ''}</Text>
                            </div>
                          )
                        )}
                        <Tooltip content="Alert group will be posted to these ChatOps channels">
                          <Icon name="info-circle" />
                        </Tooltip>
                      </HorizontalGroup>
                    )}
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
              {!escalationChainsExist && (
                <Alert severity="warning" title="Direct paging integration not configured">
                  <VerticalGroup>
                    <Text>
                      The direct paging integration for the selected team has no escalation chains configured.
                      <br />
                      If you proceed with the alert group, the team likely will not be notified. <br />
                      <a
                        href={
                          'https://grafana.com/docs/oncall/latest/integrations/manual/#learn-the-flow-and-handle-warnings'
                        }
                        target="_blank"
                        rel="noreferrer"
                        className={cx('link')}
                      >
                        <Text type="link">Learn more.</Text>
                      </a>
                    </Text>
                  </VerticalGroup>
                </Alert>
              )}
            </VerticalGroup>
          ) : (
            <Alert severity="warning" title={'Direct paging integration missing'}>
              <HorizontalGroup>
                <Text>
                  The selected team doesn't have a direct paging integration configured and will not be notified. <br />
                  If you proceed with the alert group, an empty direct paging integration will be created automatically
                  for the team. <br />
                  <a
                    href={
                      'https://grafana.com/docs/oncall/latest/integrations/manual/#learn-the-flow-and-handle-warnings'
                    }
                    target="_blank"
                    rel="noreferrer"
                    className={cx('link')}
                  >
                    <Text type="link">Learn more.</Text>
                  </a>
                </Text>
              </HorizontalGroup>
            </Alert>
          ))}
      </VerticalGroup>
    );
  };

  return (
    <Drawer scrollableContent title="Create Alert Group" onClose={onHide} closeOnMaskClick={false} width="70%">
      <VerticalGroup>
        <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
        <Field label="Team to notify">
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
          <Button type="submit" form={manualAlertFormConfig.name} disabled={!selectedTeamId}>
            Create
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Drawer>
  );
};

export default ManualAlertGroup;
