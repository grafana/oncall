import React from 'react';

import { Button, HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { MaintenanceIntegration } from 'models/alert_receive_channel';
import { Alert as AlertType, Alert, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import SilenceDropdown from 'pages/incidents/parts/SilenceDropdown';
import { move } from 'state/helpers';
import { UserAction } from 'state/userAction';

export const getIncidentStatusTag = (alert: Alert) => {
  switch (alert.status) {
    case IncidentStatus.New:
      return (
        <Tag color="#E02F44">
          <Text strong size="small">
            Firing
          </Text>
        </Tag>
      );
    case IncidentStatus.Acknowledged:
      return (
        <Tag color="#C69B06">
          <Text strong size="small">
            Acknowledged
          </Text>
        </Tag>
      );
    case IncidentStatus.Resolved:
      return (
        <Tag color="#299C46">
          <Text strong size="small">
            Resolved
          </Text>
        </Tag>
      );
    case IncidentStatus.Silenced:
      return (
        <Tag color="#464C54">
          <Text strong size="small">
            Silenced
          </Text>
        </Tag>
      );
    default:
      return null;
  }
};

export const renderRelatedUsers = (
  { related_users, resolved_by_user, acknowledged_by_user }: Alert,
  isFull = false
) => {
  let users = [...related_users];

  if (!users.length && isFull) {
    return <Text type="secondary">No users involved</Text>;
  }

  const renderUser = (user: User) => {
    let badge = undefined;
    if (resolved_by_user && user.pk === resolved_by_user.pk) {
      badge = <Icon name="check-circle" style={{ color: '#52c41a' }} />;
    } else if (acknowledged_by_user && user.pk === acknowledged_by_user.pk) {
      badge = <Icon name="eye" style={{ color: '#f2c94c' }} />;
    }

    return (
      <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} wrap={false}>
        <Text type="secondary">
          <Avatar size="small" src={user.avatar} /> {user.username} {badge}
        </Text>
      </PluginLink>
    );
  };

  if (resolved_by_user) {
    const index = users.findIndex((user) => user.pk === resolved_by_user.pk);
    if (index > -1) {
      users = move(users, index, 0);
    }
  }

  if (acknowledged_by_user) {
    const index = users.findIndex((user) => user.pk === acknowledged_by_user.pk);
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
};

export const getActionButtons = (
  { root_alert_group, loading, resolved, acknowledged, status, alert_receive_channel }: AlertType,
  cx: any,
  callbacks: { [key: string]: any }
) => {
  if (root_alert_group) {
    return null;
  }

  const { onResolve, onUnresolve, onAcknowledge, onUnacknowledge, onSilence, onUnsilence } = callbacks;

  const resolveButton = (
    <WithPermissionControl key="resolve" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={loading} onClick={onResolve} variant="primary">
        Resolve
      </Button>
    </WithPermissionControl>
  );

  const unacknowledgeButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={loading} onClick={onUnacknowledge} variant="secondary">
        Unacknowledge
      </Button>
    </WithPermissionControl>
  );

  const unresolveButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={loading} onClick={onUnresolve} variant="primary">
        Unresolve
      </Button>
    </WithPermissionControl>
  );

  const acknowledgeButton = (
    <WithPermissionControl key="acknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={loading} onClick={onAcknowledge} variant="secondary">
        Acknowledge
      </Button>
    </WithPermissionControl>
  );

  const buttons = [];

  if (alert_receive_channel.integration !== MaintenanceIntegration) {
    if (status === IncidentStatus.New) {
      buttons.push(
        <SilenceDropdown
          className={cx('silence-button-inline')}
          key="silence"
          disabled={loading}
          onSelect={onSilence}
          buttonSize="sm"
        />
      );
    }

    if (status === IncidentStatus.Silenced) {
      buttons.push(
        <WithPermissionControl key="silence" userAction={UserAction.UpdateIncidents}>
          <Button size="sm" disabled={loading} variant="secondary" onClick={onUnsilence}>
            Unsilence
          </Button>
        </WithPermissionControl>
      );
    }

    if (!resolved && !acknowledged) {
      buttons.push(acknowledgeButton, resolveButton);
    } else if (!resolved) {
      buttons.push(unacknowledgeButton, resolveButton);
    } else {
      buttons.push(unresolveButton);
    }
  } else if (!resolved) {
    buttons.push(resolveButton);
  }

  return <HorizontalGroup justify="flex-end">{buttons}</HorizontalGroup>;
};
