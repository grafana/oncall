import React, { useEffect } from 'react';

import { css } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { COLORS } from 'styles/utils.styles';

import { Text } from 'components/Text/Text';
import { WorkingHours } from 'components/WorkingHours/WorkingHours';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface UserItemProps {
  pk: ApiSchemas['User']['pk'];
  shiftColor: string;
  shiftStart: string;
  shiftEnd: string;
}

const WEEK_IN_SECONDS = 60 * 60 * 24 * 7;

export const UserItem = ({ pk, shiftColor, shiftStart, shiftEnd }: UserItemProps) => {
  const { userStore } = useStore();
  const styles = useStyles2(getStyles);

  useEffect(() => {
    if (!userStore.items[pk]) {
      userStore.fetchItemById({ userPk: pk, skipIfAlreadyPending: true });
    }
  }, []);

  const name = userStore.items[pk]?.username;
  const desc = userStore.items[pk]?.timezone;
  const workingHours = userStore.items[pk]?.working_hours;
  const timezone = userStore.items[pk]?.timezone;
  const duration = dayjs(shiftEnd).diff(dayjs(shiftStart), 'seconds');

  return (
    <div className={cx('user-item')} style={{ backgroundColor: shiftColor, width: '100%' }}>
      {duration <= WEEK_IN_SECONDS && (
        <WorkingHours
          timezone={timezone}
          workingHours={workingHours}
          startMoment={dayjs(shiftStart)}
          duration={duration}
          className={cx('working-hours')}
        />
      )}
      <div className={cx('user-title')}>
        <Text strong>{name}</Text> <Text className={styles.gray}>({desc})</Text>
      </div>
    </div>
  );
};

const getStyles = () => {
  return {
    gray: css`
      color: ${COLORS.ALWAYS_GREY};
    `,
  };
};
