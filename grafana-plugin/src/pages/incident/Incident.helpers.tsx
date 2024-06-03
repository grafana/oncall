import React from 'react';

import { css, cx } from '@emotion/css';
import { Button, HorizontalGroup, IconButton, Tooltip, VerticalGroup, useStyles2 } from '@grafana/ui';
import { getUtilStyles } from 'styles/utils.styles';

import { Avatar } from 'components/Avatar/Avatar';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { TextEllipsisTooltip } from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { SilenceButtonCascader } from 'pages/incidents/parts/SilenceButtonCascader';
import { move } from 'state/helpers';
import { UserActions } from 'utils/authorization/authorization';

export const IncidentRelatedUsers = (props: { incident: ApiSchemas['AlertGroup']; isFull: boolean }) => {
  const { incident, isFull } = props;

  const { related_users } = incident;

  const styles = useStyles2(getStyles);
  const utilStyles = useStyles2(getUtilStyles);

  let users = [...related_users];

  if (!users.length && isFull) {
    return <Text type="secondary">No users involved</Text>;
  }

  function renderUser(user: Partial<ApiSchemas['User']>) {
    let badge = undefined;
    if (incident.resolved_by_user && user.pk === incident.resolved_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Resolved" name="check-circle" style={{ color: '#52c41a' }} />;
    } else if (incident.acknowledged_by_user && user.pk === incident.acknowledged_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Acknowledged" name="eye" style={{ color: '#f2c94c' }} />;
    }

    return (
      <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} wrap={false}>
        <TextEllipsisTooltip placement="top" content={user.username}>
          <Text type="secondary" className={utilStyles.overflowChild}>
            <Avatar size="small" src={user.avatar} />{' '}
            <span className={cx(utilStyles.wordBreakAll, 'u-margin-right-xs')}>{user.username}</span>
            <span className={styles.userBadge}>{badge}</span>
          </Text>
        </TextEllipsisTooltip>
      </PluginLink>
    );
  }

  if (incident.resolved_by_user) {
    const index = users.findIndex((user) => user.pk === incident.resolved_by_user.pk);
    if (index > -1) {
      users = move(users, index, 0);
    }
  }

  if (incident.acknowledged_by_user) {
    const index = users.findIndex((user) => user.pk === incident.acknowledged_by_user.pk);
    if (index > -1) {
      users = move(users, index, 0);
    }
  }

  const visibleUsers = isFull ? users : users.slice(0, 2);
  const otherUsers = isFull ? [] : users.slice(2);

  if (isFull) {
    return (
      <>
        {visibleUsers.map((user, index) => (
          <>
            {index ? ', ' : ''}
            {renderUser(user)}
          </>
        ))}
      </>
    );
  }

  return (
    <VerticalGroup spacing="xs">
      {visibleUsers.map(renderUser)}
      {Boolean(otherUsers.length) && (
        <Tooltip
          placement="top"
          content={
            <>
              {otherUsers.map((user, index) => (
                <>
                  {index ? ', ' : ''}
                  {renderUser(user)}
                </>
              ))}
            </>
          }
        >
          <span>
            <Text type="secondary" underline size="small">
              +{otherUsers.length} user{otherUsers.length > 1 ? 's' : ''}
            </Text>
          </span>
        </Tooltip>
      )}
    </VerticalGroup>
  );
};

export function getActionButtons(
  incident: ApiSchemas['AlertGroup'],
  callbacks: { [key: string]: any },
  allSecondary = false
) {
  const { onResolve, onUnresolve, onAcknowledge, onUnacknowledge, onSilence, onUnsilence } = callbacks;

  if (incident?.root_alert_group) {
    return null;
  }

  const resolveButton = (
    <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident?.loading} onClick={onResolve} variant={allSecondary ? 'secondary' : 'primary'}>
        Resolve
      </Button>
    </WithPermissionControlTooltip>
  );

  const unacknowledgeButton = (
    <WithPermissionControlTooltip key="unacknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident?.loading} onClick={onUnacknowledge} variant="secondary">
        Unacknowledge
      </Button>
    </WithPermissionControlTooltip>
  );

  const unresolveButton = (
    <WithPermissionControlTooltip key="unresolve" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident?.loading} onClick={onUnresolve} variant={allSecondary ? 'secondary' : 'primary'}>
        Unresolve
      </Button>
    </WithPermissionControlTooltip>
  );

  const acknowledgeButton = (
    <WithPermissionControlTooltip key="acknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident?.loading} onClick={onAcknowledge} variant="secondary">
        Acknowledge
      </Button>
    </WithPermissionControlTooltip>
  );

  const silenceButton = (
    <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
      <SilenceButtonCascader disabled={incident?.loading} onSelect={onSilence} />
    </WithPermissionControlTooltip>
  );

  const unsilenceButton = (
    <WithPermissionControlTooltip key="unsilence" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident?.loading} variant="secondary" onClick={onUnsilence}>
        Unsilence
      </Button>
    </WithPermissionControlTooltip>
  );

  if (incident?.status === undefined) {
    // to render all buttons if status unknown
    return [acknowledgeButton, unacknowledgeButton, resolveButton, unresolveButton, silenceButton, unsilenceButton];
  }

  const buttons = [];

  if (incident.status === IncidentStatus.Silenced) {
    buttons.push(unsilenceButton);
  } else if (incident.status !== IncidentStatus.Resolved) {
    buttons.push(silenceButton);
  }

  if (!incident.resolved && !incident.acknowledged) {
    buttons.push(acknowledgeButton, resolveButton);
  } else if (!incident.resolved) {
    buttons.push(unacknowledgeButton, resolveButton);
  } else {
    buttons.push(unresolveButton);
  }

  return <HorizontalGroup justify="flex-end">{buttons}</HorizontalGroup>;
}

const getStyles = () => {
  return {
    userBadge: css`
      vertical-align: middle;
    `,
  };
};
