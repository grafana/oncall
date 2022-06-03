import React, { ReactElement } from 'react';

import { Button, HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { MaintenanceIntegration } from 'models/alert_receive_channel';
import { Alert as AlertType, Alert, AlertAction, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import SilenceDropdown from 'pages/incidents/parts/SilenceDropdown';
import { move } from 'state/helpers';
import { UserAction } from 'state/userAction';

const TAG_COLORS = [
  '#D32D20',
  '#1E72B8',
  '#B240A2',
  '#705DA0',
  '#466803',
  '#497A3C',
  '#3D71AA',
  '#B15415',
  '#890F02',
  '#6E6E6E',
  '#0A437C',
  '#6D1F62',
  '#584477',
  '#4C7A3F',
  '#2F4F4F',
  '#BF1B00',
  '#7662B1',
  '#8A2EB8',
  '#517A00',
  '#000000',
  '#3F6833',
  '#2F575E',
  '#99440A',
  '#AE561A',
  '#0E4AB4',
  '#58140C',
  '#052B51',
  '#511749',
  '#3F2B5B',
];

export function getIncidentStatusTag(alert: Alert) {
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
      badge = <Icon name="check-circle" style={{ color: '#52c41a' }} />;
    } else if (incident.acknowledged_by_user && user.pk === incident.acknowledged_by_user.pk) {
      badge = <Icon name="eye" style={{ color: '#f2c94c' }} />;
    }

    return (
      <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} wrap={false}>
        <Text type="secondary">
          <Avatar size="small" src={user.avatar} /> {user.username} {badge}
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

export function getActionButtons(incident: AlertType, cx: any, callbacks: { [key: string]: any }) {
  if (incident.root_alert_group) {
    return null;
  }

  const { onResolve, onUnresolve, onAcknowledge, onUnacknowledge, onSilence, onUnsilence } = callbacks;

  const resolveButton = (
    <WithPermissionControl key="resolve" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={incident.loading} onClick={onResolve} variant="primary">
        Resolve
      </Button>
    </WithPermissionControl>
  );

  const unacknowledgeButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={incident.loading} onClick={onUnacknowledge} variant="secondary">
        Unacknowledge
      </Button>
    </WithPermissionControl>
  );

  const unresolveButton = (
    <WithPermissionControl key="unacknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={incident.loading} onClick={onUnresolve} variant="primary">
        Unresolve
      </Button>
    </WithPermissionControl>
  );

  const acknowledgeButton = (
    <WithPermissionControl key="acknowledge" userAction={UserAction.UpdateIncidents}>
      <Button size="sm" disabled={incident.loading} onClick={onAcknowledge} variant="secondary">
        Acknowledge
      </Button>
    </WithPermissionControl>
  );

  const buttons = [];

  if (incident.alert_receive_channel.integration !== MaintenanceIntegration) {
    if (incident.status === IncidentStatus.New) {
      buttons.push(
        <SilenceDropdown
          className={cx('silence-button-inline')}
          key="silence"
          disabled={incident.loading}
          onSelect={onSilence}
        />
      );
    }

    if (incident.status === IncidentStatus.Silenced) {
      buttons.push(
        <WithPermissionControl key="silence" userAction={UserAction.UpdateIncidents}>
          <Button size="sm" disabled={incident.loading} variant="secondary" onClick={onUnsilence}>
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
