import React, { useCallback, useEffect } from 'react';

import { HorizontalGroup, Icon, IconButton, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './../Incident.module.scss';

const cx = cn.bind(styles);

interface PagedUsersProps {
  pagedUsers: Alert['paged_users'];
  disabled: boolean;

  onRemove: (id: User['pk']) => void;
}

const PagedUsers = observer((props: PagedUsersProps) => {
  const { pagedUsers, disabled, onRemove } = props;

  const getPagedUserRemoveHandler = useCallback((id: User['pk']) => {
    return () => {
      onRemove(id);
    };
  }, []);

  const { userStore } = useStore();

  useEffect(() => {
    pagedUsers &&
      pagedUsers.forEach((user) => {
        if (!userStore.items[user.pk]) {
          userStore.updateItem(user.pk);
        }
      });
  }, [pagedUsers]);

  if (!pagedUsers || !pagedUsers.length) {
    return null;
  }

  return (
    <div className={cx('paged-users')}>
      <Text.Title type="primary" level={4} className={cx('timeline-title')}>
        Additional responders
      </Text.Title>
      <ul className={cx('paged-users-list')}>
        {pagedUsers.map((pagedUser) => {
          const storeUser = userStore.items[pagedUser.pk];

          return (
            <li key={pagedUser.pk}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <Avatar size="big" src={pagedUser.avatar} />
                  <Text strong>{pagedUser.username}</Text>
                  {Boolean(
                    storeUser &&
                      !storeUser.notification_chain_verbal.default &&
                      !storeUser.notification_chain_verbal.important
                  ) && (
                    <Tooltip content="User doesn't have configured notification chains">
                      <Icon name="exclamation-triangle" style={{ color: 'var(--error-text-color)' }} />
                    </Tooltip>
                  )}
                </HorizontalGroup>
                <HorizontalGroup>
                  <PluginLink
                    className={cx('hover-button')}
                    target="_blank"
                    query={{ page: 'users', id: pagedUser.pk }}
                  >
                    <IconButton
                      tooltip="Open user profile in new tab"
                      style={{ color: 'var(--always-gray)' }}
                      name="external-link-alt"
                    />
                  </PluginLink>
                  <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
                    <WithConfirm
                      title={`Are you sure to remove "${pagedUser.username}" from responders?`}
                      confirmText="Remove"
                    >
                      <IconButton
                        className={cx('hover-button')}
                        onClick={getPagedUserRemoveHandler(pagedUser.pk)}
                        tooltip="Remove from responders"
                        name="trash-alt"
                        disabled={disabled}
                      />
                    </WithConfirm>
                  </WithPermissionControlTooltip>
                </HorizontalGroup>
              </HorizontalGroup>
            </li>
          );
        })}
      </ul>
    </div>
  );
});

export default PagedUsers;
