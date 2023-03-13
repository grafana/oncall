import React from 'react';

import { Icon, Label, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import ReactDOM from 'react-dom';

import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './GrafanaTeamSelect.module.scss';

const cx = cn.bind(styles);

const GrafanaTeamSelect = observer(() => {
  const store = useStore();

  const { userStore, grafanaTeamStore } = store;
  const grafanaTeams = grafanaTeamStore.getSearchResult();
  const user = userStore.currentUser;

  if (!grafanaTeams || !user) {
    return null;
  }

  const onTeamChange = async (teamId: GrafanaTeam['id']) => {
    await userStore.updateCurrentUser({ current_team: teamId });
  };

  const content = (
    <div className={cx('teamSelect')}>
      <div className={cx('teamSelectLabel')}>
        <Label>
          <span className={cx('teamSelectText')}>
            Select default Team{''}
            <Tooltip content="All objects created by you will be owned by your default team">
              <Icon name="info-circle" size="md" className={cx('teamSelectInfo')}></Icon>
            </Tooltip>
          </span>
        </Label>
        <WithPermissionControlTooltip userAction={UserActions.TeamsWrite}>
          <a href="/org/teams" className={cx('teamSelectLink')}>
            Edit teams
          </a>
        </WithPermissionControlTooltip>
      </div>
      <GSelect
        modelName="grafanaTeamStore"
        displayField="name"
        valueField="id"
        placeholder="Select Team"
        className={cx('select', 'control')}
        value={user.current_team}
        onChange={onTeamChange}
      />
    </div>
  );

  return document.getElementsByClassName('page-header__inner')[0]
    ? ReactDOM.createPortal(content, document.getElementsByClassName('page-header__inner')[0])
    : isTopNavbar()
    ? content
    : null;
});

export default GrafanaTeamSelect;
