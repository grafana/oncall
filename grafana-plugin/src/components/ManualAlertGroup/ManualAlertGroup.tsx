import React, { FC, useCallback, useState } from 'react';

import {
  Alert,
  Button,
  Drawer,
  Field,
  HorizontalGroup,
  IconButton,
  Label,
  LoadingPlaceholder,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

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
import { useStore } from 'state/useStore';

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
  const data = { team: store.userStore.currentUser?.current_team };

  const [selectedTeamId, setSelectedTeam] = useState<GrafanaTeam['id']>();
  const [selectedTeamDirectPaging, setSelectedTeamDirectPaging] = useState<AlertReceiveChannel>();
  const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  const handleFormSubmit = async (data) => {
    store.directPagingStore
      .createManualAlertRule(prepareForUpdate(userResponders, scheduleResponders, data))
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

  const warningTitle = (
    <>
      <TeamName team={store.grafanaTeamStore.items[selectedTeamId]} />{' '}
      <Text>team doesn't have the the Direct Paging integration yet</Text>
    </>
  );

  const DirectPagingIntegrationVariants = observer(({ selectedTeamId, selectedTeamDirectPaging }) => {
    return (
      <VerticalGroup>
        {selectedTeamId &&
          (directPagingLoading ? (
            <LoadingPlaceholder text="Loading..." />
          ) : selectedTeamDirectPaging ? (
            <DirectPagingIntegration data={selectedTeamDirectPaging} />
          ) : (
            <Alert severity="warning" title={warningTitle}>
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
  });

  const DirectPagingIntegration = ({ data }) => {
    return (
      <VerticalGroup>
        <Label>Team will be notified according to the integration settings:</Label>
        <ul className={cx('responders-list')}>
          <li>
            <HorizontalGroup justify="space-between">
              <Text>{data?.verbal_name}</Text>
              <HorizontalGroup>
                <PluginLink target="_blank" query={{ page: 'integrations', id: data.id }}>
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
      </VerticalGroup>
    );
  };

  return (
    <>
      <Drawer
        scrollableContent
        title="Create alert group (Direct Paging)"
        onClose={onHide}
        closeOnMaskClick={false}
        width={'70%'}
      >
        <VerticalGroup>
          <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
          <Field label="Select team you want to notify">
            <GrafanaTeamSelect withoutModal onSelect={onUpdateSelectedTeam} />
          </Field>
          <DirectPagingIntegrationVariants
            selectedTeamId={selectedTeamId}
            selectedTeamDirectPaging={selectedTeamDirectPaging}
          />

          <EscalationVariants
            value={{ userResponders, scheduleResponders }}
            onUpdateEscalationVariants={onUpdateEscalationVariants}
            variant={
              (selectedTeamId && selectedTeamDirectPaging) || userResponders.length || scheduleResponders.length
                ? 'secondary'
                : 'primary'
            }
            withLabels={true}
          />
          <HorizontalGroup justify="flex-end">
            <Button variant="secondary" onClick={onHide}>
              Cancel
            </Button>
            <Button
              type="submit"
              form={manualAlertFormConfig.name}
              disabled={
                !((selectedTeamId && selectedTeamDirectPaging) || userResponders.length || scheduleResponders.length)
              }
            >
              Create
            </Button>
          </HorizontalGroup>
        </VerticalGroup>
      </Drawer>
    </>
  );
};

export default ManualAlertGroup;
