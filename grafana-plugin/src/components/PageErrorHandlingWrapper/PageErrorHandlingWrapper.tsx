import React, { useEffect } from 'react';

import { Button, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { PropTypes } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { ChangeTeamIcon } from 'icons';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils';

import styles from './PageErrorHandlingWrapper.module.css';

const cx = cn.bind(styles);

export interface PageBaseState {
  errorData: PageErrorData;
}

export interface PageErrorData {
  isNotFoundError?: boolean;
  isWrongTeamError?: boolean;
  wrongTeamNoPermissions?: boolean;
  switchToTeam?: { name: string; id: string };
}

export default function PageErrorHandlingWrapper({
  errorData,
  objectName,
  pageName,
  itemNotFoundMessage,
  children,
}: {
  errorData: PageErrorData;
  objectName: string;
  pageName: string;
  itemNotFoundMessage?: string;
  children: () => JSX.Element;
}) {
  useEffect(() => {
    const { isWrongTeamError, isNotFoundError } = errorData;
    if (!isWrongTeamError && isNotFoundError && itemNotFoundMessage) {
      openWarningNotification(itemNotFoundMessage);
    }
  }, [errorData.isNotFoundError]);

  const store = useStore();

  if (!errorData.isWrongTeamError) {return children();}

  const currentTeamId = store.userStore.currentUser?.current_team;
  const currentTeam = store.grafanaTeamStore.items[currentTeamId]?.name;

  const { switchToTeam, wrongTeamNoPermissions } = errorData;

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
        <Text type="secondary">
          Or return to the <PluginLink query={{ page: pageName }}>{objectName} list</PluginLink> for team {currentTeam}
        </Text>
      </VerticalGroup>
    </div>
  );
}
