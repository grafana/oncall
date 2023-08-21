import React from 'react';

import { Button, HorizontalGroup, IconButton, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import { MatchMediaTooltip } from 'components/MatchMediaTooltip/MatchMediaTooltip';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert as AlertType, Alert, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { SilenceButtonCascader } from 'pages/incidents/parts/SilenceButtonCascader';
import { move } from 'state/helpers';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';
import { TABLE_COLUMN_MAX_WIDTH } from 'utils/consts';

import styles from './Incident.module.scss';

const cx = cn.bind(styles);

export function getIncidentStatusTag(alert: Alert) {
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

export function renderRelatedUsers(incident: Alert, isFull = false) {
  const { related_users } = incident;

  let users = [...related_users];

  if (!users.length && isFull) {
    return <Text type="secondary">No users involved</Text>;
  }

  function renderUser(user: User) {
    let badge = undefined;
    if (incident.resolved_by_user && user.pk === incident.resolved_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Resolved" name="check-circle" style={{ color: '#52c41a' }} />;
    } else if (incident.acknowledged_by_user && user.pk === incident.acknowledged_by_user.pk) {
      badge = <IconButton tooltipPlacement="top" tooltip="Acknowledged" name="eye" style={{ color: '#f2c94c' }} />;
    }

    return (
      <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} wrap={false} className="table__email-content">
        <Text type="secondary">
          <Avatar size="small" src={user.avatar} />{' '}
          <MatchMediaTooltip placement="top" content={user.username} maxWidth={TABLE_COLUMN_MAX_WIDTH}>
            <span>{user.username}</span>
          </MatchMediaTooltip>{' '}
          {badge}
        </Text>
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
    <div className={'table__email-column'}>
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
    </div>
  );
}

export function getActionButtons(incident: AlertType, cx: any, callbacks: { [key: string]: any }) {
  if (incident.root_alert_group) {
    return null;
  }

  const { onResolve, onUnresolve, onAcknowledge, onUnacknowledge, onSilence, onUnsilence } = callbacks;

  const resolveButton = (
    <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading || incident.is_restricted} onClick={onResolve} variant="primary">
        Resolve
      </Button>
    </WithPermissionControlTooltip>
  );

  const unacknowledgeButton = (
    <WithPermissionControlTooltip key="unacknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading || incident.is_restricted} onClick={onUnacknowledge} variant="secondary">
        Unacknowledge
      </Button>
    </WithPermissionControlTooltip>
  );

  const unresolveButton = (
    <WithPermissionControlTooltip key="unacknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading || incident.is_restricted} onClick={onUnresolve} variant="primary">
        Unresolve
      </Button>
    </WithPermissionControlTooltip>
  );

  const acknowledgeButton = (
    <WithPermissionControlTooltip key="acknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading || incident.is_restricted} onClick={onAcknowledge} variant="secondary">
        Acknowledge
      </Button>
    </WithPermissionControlTooltip>
  );

  const buttons = [];

  if (incident.status === IncidentStatus.Silenced) {
    buttons.push(
      <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
        <Button disabled={incident.loading || incident.is_restricted} variant="secondary" onClick={onUnsilence}>
          Unsilence
        </Button>
      </WithPermissionControlTooltip>
    );
  } else if (incident.status !== IncidentStatus.Resolved) {
    buttons.push(
      <SilenceButtonCascader
        className={cx('silence-button-inline')}
        key="silence"
        disabled={incident.loading || incident.is_restricted}
        onSelect={onSilence}
      />
    );
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
