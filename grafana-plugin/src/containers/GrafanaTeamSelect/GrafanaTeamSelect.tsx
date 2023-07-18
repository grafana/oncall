import React, { useCallback, useState } from 'react';

import { Button, HorizontalGroup, Icon, Label, Modal, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './GrafanaTeamSelect.module.scss';

const cx = cn.bind(styles);

interface GrafanaTeamSelectProps {
  onSelect: (id: GrafanaTeam['id']) => void;
  onHide?: () => void;
  withoutModal?: boolean;
  defaultValue?: GrafanaTeam['id'];
}

const GrafanaTeamSelect = observer(({ onSelect, onHide, withoutModal, defaultValue }: GrafanaTeamSelectProps) => {
  const store = useStore();

  const { userStore, grafanaTeamStore } = store;
  const user = userStore.currentUser;

  const [selectedTeam, setSelectedTeam] = useState<GrafanaTeam['id']>(defaultValue);

  const grafanaTeams = grafanaTeamStore.getSearchResult();

  const handleTeamSelect = useCallback(
    (value) => {
      setSelectedTeam(value);

      if (withoutModal) {
        onSelect(value);
      }
    },
    [onSelect, withoutModal]
  );

  const handleConfirm = useCallback(() => {
    onSelect(selectedTeam);
  }, [onSelect, selectedTeam]);

  if (!grafanaTeams || !user) {
    return null;
  }

  const select = (
    <GSelect
      showSearch
      modelName="grafanaTeamStore"
      displayField="name"
      valueField="id"
      placeholder="Select team"
      className={cx('select', 'control')}
      value={selectedTeam}
      onChange={handleTeamSelect}
    />
  );

  if (withoutModal) {
    return select;
  }

  return (
    <Modal onDismiss={onHide} closeOnEscape isOpen title="Select team" className={cx('root')}>
      <VerticalGroup>
        <Label>
          <span className={cx('teamSelectText')}>
            Select team{''}
            <Tooltip content="It will also update your default team">
              <Icon name="info-circle" size="md" className={cx('teamSelectInfo')}></Icon>
            </Tooltip>
          </span>
        </Label>
        <div className={cx('teamSelect')}>{select}</div>
        <WithPermissionControlTooltip userAction={UserActions.TeamsWrite}>
          <a href="/org/teams" className={cx('teamSelectLink')}>
            Edit teams
          </a>
        </WithPermissionControlTooltip>
        <HorizontalGroup justify="flex-end">
          <Button variant="primary" onClick={handleConfirm}>
            Ok
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
});

export default GrafanaTeamSelect;
