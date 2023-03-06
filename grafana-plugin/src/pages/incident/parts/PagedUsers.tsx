import React, { useCallback } from 'react';

import { HorizontalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { UserActions } from 'utils/authorization';

import styles from './../Incident.module.scss';

const cx = cn.bind(styles);

interface PagedUsersProps {
  pagedUsers: Alert['paged_users'];
  onRemove: (id: User['pk']) => void;
}

const PagedUsers = (props: PagedUsersProps) => {
  const { pagedUsers, onRemove } = props;

  const getPagedUserRemoveHandler = useCallback((id: User['pk']) => {
    return () => {
      onRemove(id);
    };
  }, []);

  if (!pagedUsers || !pagedUsers.length) {
    return null;
  }

  return (
    <div className={cx('paged-users')}>
      <Text.Title type="primary" level={4} className={cx('timeline-title')}>
        Current responders
      </Text.Title>
      <ul className={cx('paged-users-list')}>
        {pagedUsers.map((pagedUser) => (
          <li key={pagedUser.pk}>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup>
                <Avatar size="big" src={pagedUser.avatar} />
                <Text strong>{pagedUser.username}</Text>
              </HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
                <WithConfirm
                  title={`Are you sure to remove "${pagedUser.username}" from responders?`}
                  confirmText="Remove"
                >
                  <IconButton
                    onClick={getPagedUserRemoveHandler(pagedUser.pk)}
                    tooltip="Remove from responders"
                    name="trash-alt"
                  />
                </WithConfirm>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PagedUsers;
