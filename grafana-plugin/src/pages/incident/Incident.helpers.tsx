import React from 'react';

import { Button, HorizontalGroup, IconButton, Tooltip, VerticalGroup } from '@grafana/ui';

import Avatar from 'components/Avatar/Avatar';
import { MatchMediaTooltip } from 'components/MatchMediaTooltip/MatchMediaTooltip';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { MaintenanceIntegration } from 'models/alert_receive_channel';
import { Alert as AlertType, Alert, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { SilenceButtonCascader } from 'pages/incidents/parts/SilenceButtonCascader';
import { move } from 'state/helpers';
import { UserActions } from 'utils/authorization';
import { TABLE_COLUMN_MAX_WIDTH } from 'utils/consts';

export function getIncidentStatusTag(alert: Alert) {
  switch (alert.status) {
    case IncidentStatus.Firing:
      return (
        <Tag color={getComputedStyle(document.documentElement).getPropertyValue('--tag-danger')}>
          <Text strong size="small">
            Firing
          </Text>
        </Tag>
      );
    case IncidentStatus.Acknowledged:
      return (
        <Tag color={getComputedStyle(document.documentElement).getPropertyValue('--tag-warning')}>
          <Text strong size="small">
            Acknowledged
          </Text>
        </Tag>
      );
    case IncidentStatus.Resolved:
      return (
        <Tag color={getComputedStyle(document.documentElement).getPropertyValue('--tag-primary')}>
          <Text strong size="small">
            Resolved
          </Text>
        </Tag>
      );
    case IncidentStatus.Silenced:
      return (
        <Tag color={getComputedStyle(document.documentElement).getPropertyValue('--tag-secondary')}>
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
    <WithPermissionControl key="resolve" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading} onClick={onResolve} variant="primary">
        Resolve
      </Button>
    </WithPermissionControl>
  );

  const unacknowledgeButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading} onClick={onUnacknowledge} variant="secondary">
        Unacknowledge
      </Button>
    </WithPermissionControl>
  );

  const unresolveButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading} onClick={onUnresolve} variant="primary">
        Unresolve
      </Button>
    </WithPermissionControl>
  );

  const acknowledgeButton = (
    <WithPermissionControl key="acknowledge" userAction={UserActions.AlertGroupsWrite}>
      <Button disabled={incident.loading} onClick={onAcknowledge} variant="secondary">
        Acknowledge
      </Button>
    </WithPermissionControl>
  );

  const buttons = [];

  if (incident.alert_receive_channel.integration !== MaintenanceIntegration) {
    if (incident.status === IncidentStatus.Firing) {
      buttons.push(
        <SilenceButtonCascader
          className={cx('silence-button-inline')}
          key="silence"
          disabled={incident.loading}
          onSelect={onSilence}
        />
      );
    }

    if (incident.status === IncidentStatus.Silenced) {
      buttons.push(
        <WithPermissionControl key="silence" userAction={UserActions.AlertGroupsWrite}>
          <Button disabled={incident.loading} variant="secondary" onClick={onUnsilence}>
            Unsilence
          </Button>
        </WithPermissionControl>
      );
    }

    if (!incident.resolved && !incident.acknowledged) {
      buttons.push(acknowledgeButton, resolveButton);
    } else if (!incident.resolved) {
      buttons.push(unacknowledgeButton, resolveButton);
    } else {
      buttons.push(unresolveButton);
    }
  } else if (!incident.resolved) {
    buttons.push(resolveButton);
  }

  return <HorizontalGroup justify="flex-end">{buttons}</HorizontalGroup>;
}
