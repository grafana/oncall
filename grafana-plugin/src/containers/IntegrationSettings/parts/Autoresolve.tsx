import React, { useCallback, useState, useEffect } from 'react';

import { Alert, Button, Icon, Label, Modal, Select } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { Team } from 'models/team/team.types';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

import styles from 'containers/IntegrationSettings/parts/Autoresolve.module.css';

const cx = cn.bind(styles);

interface AutoresolveProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  alertGroupId?: AlertType['pk'];
  onSwitchToTemplate?: (templateName: string) => void;
}

const Autoresolve = ({ alertReceiveChannelId, onSwitchToTemplate, alertGroupId }: AutoresolveProps) => {
  const store = useStore();
  const { alertReceiveChannelStore, grafanaTeamStore, userStore } = store;

  const currentTeam = userStore.currentUser?.current_team;

  const alertReceiveChannel = alertReceiveChannelStore.items[alertReceiveChannelId];

  const [teamId, setTeamId] = useState<Team['pk']>(currentTeam);
  const [showSaveConfirmationModal, setShowSaveConfirmationModal] = useState<boolean>(false);
  const [autoresolveChanged, setAutoresolveChanged] = useState<boolean>(false);
  const [autoresolveValue, setAutoresolveValue] = useState<boolean>(alertReceiveChannel?.allow_source_based_resolving);
  const [showErrorOnTeamSelect, setShowErrorOnTeamSelect] = useState<boolean>(false);
  const [autoresolveSelected, setAutoresolveSelected] = useState<boolean>(
    alertReceiveChannel?.allow_source_based_resolving
  );
  const [autoresolveConditionInvalid, setAutoresolveConditionInvalid] = useState<boolean>(false);

  useEffect(() => {
    store.alertReceiveChannelStore.updateItem(alertReceiveChannelId);
    store.alertReceiveChannelStore.updateTemplates(alertReceiveChannelId, alertGroupId);
  }, [alertGroupId, alertReceiveChannelId, store]);

  useEffect(() => {
    const autoresolveCondition = get(
      store.alertReceiveChannelStore.templates[alertReceiveChannelId],
      'resolve_condition_template'
    );
    if (autoresolveCondition === 'invalid template') {
      setAutoresolveConditionInvalid(true);
    }
  }, [store.alertReceiveChannelStore.templates[alertReceiveChannelId]]);

  const handleAutoresolveSelected = useCallback(
    (autoresolveSelectedOption) => {
      setAutoresolveChanged(true);
      setAutoresolveValue(autoresolveSelectedOption?.value);
      if (autoresolveSelectedOption?.value === 'true') {
        setAutoresolveSelected(true);
      }
      if (autoresolveSelectedOption?.value === 'false') {
        setAutoresolveSelected(false);
      }
    },
    [autoresolveChanged]
  );

  const handleChangeTeam = useCallback(
    (value: Team['pk']) => {
      setTeamId(value);
    },
    [teamId]
  );

  const handleSaveTeam = () => {
    store.alertReceiveChannelStore
      .changeTeam(alertReceiveChannelId, teamId)
      .then(async () => {
        await alertReceiveChannelStore.updateItems();
        setShowSaveConfirmationModal(false);
        openNotification(
          `Integration moved from ${grafanaTeamStore.items[currentTeam]?.name} to ${grafanaTeamStore.items[teamId]?.name}`
        );
        if (alertReceiveChannelId === store.selectedAlertReceiveChannel) {
          const searchResult = alertReceiveChannelStore.getSearchResult();

          store.selectedAlertReceiveChannel = searchResult && searchResult[0] && searchResult[0].id;
        }
      })
      .catch((error) => {
        openErrorNotification(get(error, 'response.data.detail'));
        setShowSaveConfirmationModal(false);
        setShowErrorOnTeamSelect(true);
      });
  };

  const handleSaveClick = () => {
    if (teamId !== currentTeam) {
      setShowSaveConfirmationModal(true);
    }
    if (autoresolveChanged) {
      store.alertReceiveChannelStore.saveAlertReceiveChannel(alertReceiveChannelId, {
        allow_source_based_resolving: autoresolveValue,
      });
    }
  };

  const handleGoToTemplateSettingsCllick = () => {
    LocationHelper.update({ tab: 'Templates' }, 'partial');
    onSwitchToTemplate('resolve_condition_template');
  };

  return (
    <>
      <Block>
        <div className={cx('border-container')}>
          <Label>
            <div className={cx('settings-label')}>
              OnCall team
              <Text type="secondary">Which team should this integration belong to?</Text>
            </div>
          </Label>
          <GSelect
            modelName="grafanaTeamStore"
            displayField="name"
            valueField="id"
            showSearch
            allowClear
            placeholder="Select a team"
            className={cx('team-select')}
            onChange={handleChangeTeam}
            value={teamId}
            showError={showErrorOnTeamSelect}
          />
        </div>
        <div className={cx('border-container')}>
          <Label>
            <div className={cx('settings-label')}>
              Autoresolve
              <Text type="secondary">How should this integration resolve incidents?</Text>
            </div>
          </Label>
          <div className={cx('team-select')}>
            <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
              <Select
                className={cx('team-select')}
                //@ts-ignore
                onChange={handleAutoresolveSelected}
                placeholder="Choose autoresolve policy"
                defaultValue={{ value: 'true', label: 'Automatically resolve' }}
                value={autoresolveValue.toString()}
                options={[
                  { value: 'true', label: 'Resolve automatically' },
                  { value: 'false', label: 'Resolve manually' },
                ]}
              />
            </WithPermissionControlTooltip>
          </div>
          {autoresolveSelected && (
            <>
              <Block shadowed bordered className={cx('autoresolve-block')}>
                <div>
                  <Text type="secondary" size="small">
                    <Icon name="info-circle" /> Incident will be automatically resolved when it matches{' '}
                  </Text>
                  <Button fill="text" size="sm" onClick={handleGoToTemplateSettingsCllick}>
                    autoresolve condition
                  </Button>
                </div>
              </Block>
              {autoresolveConditionInvalid && (
                <Block shadowed bordered className={cx('autoresolve-block')}>
                  <div>
                    <Text type="secondary" size="small">
                      <Icon name="exclamation-triangle" className={cx('warning-icon-color')} /> Autoresolving condition
                      template is invalid, please{' '}
                    </Text>
                    <Button fill="text" size="sm" onClick={handleGoToTemplateSettingsCllick}>
                      Edit it
                    </Button>
                  </div>
                </Block>
              )}
            </>
          )}
        </div>
        <div className={cx('team-select-actionbuttons')}>
          <Button variant="primary" onClick={handleSaveClick}>
            Save changes
          </Button>
        </div>
      </Block>
      {showSaveConfirmationModal && (
        <Modal
          isOpen
          title="Are you sure you want to move this integration to another team?"
          onDismiss={() => setShowSaveConfirmationModal(false)}
        >
          <div className={cx('root')}>
            <Alert title="When changing the onCall team" severity="info">
              <ul>
                <li>
                  If this integration is linked to multiple escalation chains belonging to its current team, you cannot
                  move it.
                </li>
                <li>If this integration is linked to users belonging to its current team, you cannot move it.</li>
                <li>The selected schedule will remain the same, even if it’s from another team.</li>
                <li>Any outgoing webhooks will remain the same, even if it’s from another team.</li>
              </ul>
            </Alert>
            <div className={cx('confirmation-buttons')}>
              <Button variant="primary" onClick={handleSaveTeam} className={cx('save-team-button')}>
                Save now
              </Button>
              <Button variant="secondary" onClick={() => setShowSaveConfirmationModal(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};

export default Autoresolve;
