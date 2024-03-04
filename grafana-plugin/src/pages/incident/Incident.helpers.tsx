import React from 'react';

import { Button, HorizontalGroup, IconButton, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import { Avatar } from 'components/Avatar/Avatar';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { TextEllipsisTooltip } from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { SilenceButtonCascader } from 'pages/incidents/parts/SilenceButtonCascader';
import { move } from 'state/helpers';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization/authorization';
import { TEXT_ELLIPSIS_CLASS } from 'utils/consts';

import styles from './Incident.module.scss';

const cx = cn.bind(styles);

export function getIncidentStatusTag(alert: ApiSchemas['AlertGroup']) {
  switch (alert.status) {
    case IncidentStatus.Firing:
      return (
        <Tag color={getVar('--tag-danger')} className={cx('status-tag')}>
          <Text strong size="small">
            Firing
          </Text>
        </Tag>
      );
    case IncidentStatus.Acknowledged:
      return (
        <Tag color={getVar('--tag-warning')} className={cx('status-tag')}>
          <Text strong size="small">
            Acknowledged
          </Text>
        </Tag>
      );
    case IncidentStatus.Resolved:
      return (
        <Tag color={getVar('--tag-primary')} className={cx('status-tag')}>
          <Text strong size="small">
            Resolved
          </Text>
        </Tag>
      );
    case IncidentStatus.Silenced:
      return (
        <Tag color={getVar('--tag-secondary')} className={cx('status-tag')}>
          <Text strong size="small">
            Silenced
          </Text>
        </Tag>
      );
    default:
      return null;
  }
}

export function renderRelatedUsers(incident: ApiSchemas['AlertGroup'], isFull = false) {
  const { related_users } = incident;

  let users = [...related_users];

  if (!users.length && isFull) {
    return <Text type="secondary">No users involved</Text>;
  }

  function renderUser(user: Partial<User>) {
    let badge = undefined;
    if (incident.resolved_by_user && user.pk === incident.resolved_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Resolved" name="check-circle" style={{ color: '#52c41a' }} />;
    } else if (incident.acknowledged_by_user && user.pk === incident.acknowledged_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Acknowledged" name="eye" style={{ color: '#f2c94c' }} />;
    }

    return (
      <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} wrap={false}>
        <TextEllipsisTooltip placement="top" content={user.username}>
          <Text type="secondary" className={cx(TEXT_ELLIPSIS_CLASS)}>
            <Avatar size="small" src={user.avatar} />{' '}
            <span className={cx('break-word', 'u-margin-right-xs')}>{user.username}</span>
            <span className={cx('user-badge')}>{badge}</span>
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
    return visibleUsers.map((user, index) => (
      <>
        {index ? ', ' : ''}
        {renderUser(user)}
      </>
    ));
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
}

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
