import React, { FC, useCallback, useEffect, useMemo } from 'react';

import { Button, HorizontalGroup, Icon, Modal, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text from 'components/Text/Text';
import { UserAvailability } from 'containers/EscalationVariants/EscalationVariants.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './UserWarning.module.scss';

interface UserWarningProps {
  onHide: () => void;
  user: User;
  userAvailability: UserAvailability;
  onUserSelect: (user: User) => void;
}

const cx = cn.bind(styles);

const UserWarning: FC<UserWarningProps> = (props) => {
  const { onHide, user, userAvailability, onUserSelect } = props;
  const store = useStore();

  const { userStore } = store;

  const getUserSelectHandler = useCallback(
    (userId: User['pk']) => {
      return async () => {
        onHide();

        if (!userStore.items[userId]) {
          await userStore.updateItem(userId);
        }

        const user = userStore.items[userId];

        onUserSelect(user);
      };
    },
    [userStore.items]
  );

  const showUserHasNoNotificationPolicyWarning = useMemo(
    () => userAvailability.warnings.some((warning) => warning.error === 'USER_HAS_NO_NOTIFICATION_POLICY'),
    [userAvailability]
  );

  const showUserIsNotOncallWarning = useMemo(
    () => userAvailability.warnings.some((warning) => warning.error === 'USER_IS_NOT_ON_CALL'),
    [userAvailability]
  );

  const userSchedules = useMemo(
    () =>
      userAvailability.warnings.reduce((memo, warning) => {
        if (warning.error === 'USER_IS_NOT_ON_CALL') {
          const schedules = warning.data.schedules;
          const userSchedulesKeys = Object.keys(schedules).filter((key: string) => schedules[key].includes(user.pk));
          memo.push(...userSchedulesKeys);
        }
        return memo;
      }, []),
    [userAvailability]
  );

  const recommendedUsers = useMemo(
    () =>
      userAvailability.warnings.reduce((memo, warning) => {
        if (warning.error === 'USER_IS_NOT_ON_CALL') {
          const users = Object.keys(warning.data.schedules).reduce((memo, key) => {
            const users = warning.data.schedules[key];
            memo.push(...users);

            return memo;
          }, []);
          memo.push(...users);
        }

        return memo;
      }, []),
    [userAvailability]
  );

  return (
    <Modal isOpen title="Add responder" onDismiss={onHide} className={cx('modal')}>
      <VerticalGroup className={cx('user-warning')}>
        {showUserHasNoNotificationPolicyWarning && (
          <HorizontalGroup>
            <Icon name="exclamation-triangle" style={{ color: 'var(--error-text-color)' }} />
            <Text>
              <Text strong>{user.username}</Text> has no notification policy
            </Text>
          </HorizontalGroup>
        )}
        {showUserIsNotOncallWarning && (
          <HorizontalGroup>
            <Icon name="exclamation-triangle" style={{ color: 'orange' }} />
            <Text>
              <Text strong>
                {user.username} (Local time {dayjs().tz(user.timezone).format('HH:mm:ss')})
              </Text>{' '}
              is not currently on-call.
            </Text>
          </HorizontalGroup>
        )}
        {userSchedules.length && (
          <HorizontalGroup>
            <Icon name="calendar-alt" />
            <Text>
              <Text strong>{user.username}</Text> appears in <Text strong>{userSchedules.join(', ')} </Text>
            </Text>
          </HorizontalGroup>
        )}
        {recommendedUsers.length && (
          <HorizontalGroup>
            <Icon name="info-circle" />
            <Text>Recommended on-call users:</Text>
          </HorizontalGroup>
        )}
        {recommendedUsers.length && (
          <ul className={cx('users')}>
            {recommendedUsers.map((userPk) => (
              <RecommendedUser key={userPk} pk={userPk} onSelect={getUserSelectHandler(userPk)} />
            ))}
          </ul>
        )}
        <Text>
          <HorizontalGroup>
            <Icon name="question-circle" />
            <Text>
              Are you sure you want to select <Text strong>{user.username}</Text>?
            </Text>
          </HorizontalGroup>
        </Text>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={getUserSelectHandler(user.pk)}>
            Confirm
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

const RecommendedUser = ({ pk, onSelect }: { pk: User['pk']; onSelect: () => void }) => {
  const store = useStore();

  const { userStore } = store;

  useEffect(() => {
    if (!userStore.items[pk]) {
      userStore.updateItem(pk);
    }
  }, [pk]);

  const user = userStore.items[pk];

  return (
    <li>
      <HorizontalGroup justify="space-between">
        <HorizontalGroup spacing="sm">
          <div className={cx('dot')} />
          <Text strong>{user?.username}</Text>
          <Text>
            ({getTzOffsetString(dayjs().tz(user?.timezone))}, {user?.timezone})
          </Text>
          <Icon name="calendar-alt" />
        </HorizontalGroup>
        <Button size="sm" onClick={onSelect}>
          Select
        </Button>
      </HorizontalGroup>
    </li>
  );
};

export default UserWarning;
