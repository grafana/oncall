import React, { useCallback, useState } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, Icon, Label, Modal, Tooltip, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';

interface GrafanaTeamSelectProps {
  onSelect: (id: GrafanaTeam['id']) => void;
  onHide?: () => void;
  withoutModal?: boolean;
  defaultValue?: GrafanaTeam['id'];
}

export const GrafanaTeamSelect = observer(
  ({ onSelect, onHide, withoutModal, defaultValue }: GrafanaTeamSelectProps) => {
    const store = useStore();
    const styles = useStyles2(getTeamStyles);

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
      <Modal onDismiss={onHide} closeOnEscape isOpen title="Select team" className={styles.root}>
        <Stack direction="column">
          <Label>
            <span>
              Select team{''}
              <Tooltip content="It will also update your default team">
                <Icon name="info-circle" size="md" className={styles.teamSelectInfo}></Icon>
              </Tooltip>
            </span>
          </Label>
          <div>{select}</div>
          <WithPermissionControlTooltip userAction={UserActions.TeamsWrite}>
            <a href="/org/teams" className={styles.teamSelectLink}>
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

const getTeamStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      width: 400px;
    `,

    teamSelectLabel: css`
      display: flex;
    `,

    teamSelectLink: css`
      color: ${theme.colors.text.primary};
    `,

    teamSelectInfo: css`
      margin-left: 4px;
    `,
  };
};
