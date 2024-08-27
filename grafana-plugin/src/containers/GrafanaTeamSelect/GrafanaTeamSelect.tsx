import React, { useCallback, useState } from 'react';

import { Button, Icon, Label, Modal, Tooltip, Stack } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import styles from './GrafanaTeamSelect.module.scss';

const cx = cn.bind(styles);

interface GrafanaTeamSelectProps {
  onSelect: (id: GrafanaTeam['id']) => void;
  onHide?: () => void;
  withoutModal?: boolean;
  defaultValue?: GrafanaTeam['id'];
}

export const GrafanaTeamSelect = observer(
  ({ onSelect, onHide, withoutModal, defaultValue }: GrafanaTeamSelectProps) => {
    const store = useStore();

    const {
      userStore,
      grafanaTeamStore,
      // dereferencing items is needed to rerender GSelect
      grafanaTeamStore: { items: grafanaTeamItems },
    } = store;
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
      <GSelect<GrafanaTeam>
        items={grafanaTeamItems}
        fetchItemsFn={grafanaTeamStore.updateItems}
        fetchItemFn={grafanaTeamStore.fetchItemById}
        getSearchResult={grafanaTeamStore.getSearchResult}
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
        <Stack direction="column">
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
          <Stack justifyContent="flex-end">
            <Button variant="primary" onClick={handleConfirm}>
              Ok
            </Button>
          </Stack>
        </Stack>
      </Modal>
    );
  }
);
