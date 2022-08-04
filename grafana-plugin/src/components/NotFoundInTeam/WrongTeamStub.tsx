import React, { FC } from 'react';

import { Button, VerticalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { ChangeTeamIcon } from 'icons';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';

import styles from './WrongTeamStub.module.css';

const cx = cn.bind(styles);

export interface WrongTeamStubProps {
  className?: string;
  objectName: string;
  pageName: string;
  currentTeam?: string;
  switchToTeam?: { name: string; id: string };
  wrongTeamNoPermissions?: boolean;
}

const WrongTeamStub: FC<WrongTeamStubProps> = (props) => {
  const store = useStore();
  const { objectName, pageName, currentTeam, switchToTeam, className, wrongTeamNoPermissions } = props;

  const onTeamChange = async (teamId: GrafanaTeam['id']) => {
    await store.userStore.updateCurrentUser({ current_team: teamId });
    window.location.reload();
  };

  return (
    <div className={cx('not-found')}>
      <VerticalGroup spacing="lg" align="center">
        <Text.Title level={1} className={cx('error-code')}>
          403
        </Text.Title>
        {wrongTeamNoPermissions && (
          <Text.Title level={4}>
            This {objectName} belongs to a team you are not a part of. Please contact your organization administrator to
            request access to the team.
          </Text.Title>
        )}
        {switchToTeam && (
          <Text.Title level={4}>
            This {objectName} belongs to team {switchToTeam.name}. To see {objectName} details please change the team to{' '}
            {switchToTeam.name}.
          </Text.Title>
        )}
        {switchToTeam && (
          <Button onClick={() => onTeamChange(switchToTeam.id)} className={cx('change-team-button')}>
            <div className={cx('change-team-icon')}>
              <ChangeTeamIcon />
            </div>
            Change the team
          </Button>
        )}
        <Text type="secondary" className={cx('return-to-list')}>
          Or return to the <PluginLink query={{ page: pageName }}>{objectName} list</PluginLink> for team {currentTeam}
        </Text>
      </VerticalGroup>
    </div>
  );
};

export default WrongTeamStub;
