import React, { useEffect } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface UserItemProps {
  pk: User['pk'];
  shiftColor: string;
  shiftStart: string;
  shiftEnd: string;
}

const UserItem = ({ pk, shiftColor, shiftStart, shiftEnd }: UserItemProps) => {
  const { userStore } = useStore();

  useEffect(() => {
    if (!userStore.items[pk]) {
      userStore.updateItem(pk);
    }
  }, []);

  const name = userStore.items[pk]?.username;
  const desc = userStore.items[pk]?.timezone;
  const workingHours = userStore.items[pk]?.working_hours;
  const timezone = userStore.items[pk]?.timezone;

  return (
    <>
      <div className={cx('user-title')}>
        <Text strong>{name}</Text> <Text style={{ color: 'var(--always-gray)' }}>({desc})</Text>
      </div>
      <WorkingHours
        timezone={timezone}
        workingHours={workingHours}
        startMoment={dayjs(shiftStart)}
        duration={dayjs(shiftEnd).diff(dayjs(shiftStart), 'seconds')}
        className={cx('working-hours')}
        style={{ backgroundColor: shiftColor }}
      />
    </>
  );
};

export default UserItem;
