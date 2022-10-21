import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';

import styles from './ScheduleUserDetails.module.css';

interface ScheduleUserDetailsProps {
  currentMoment: dayjs.Dayjs;
  user: User;
}

const cx = cn.bind(styles);

const ScheduleUserDetails: FC<ScheduleUserDetailsProps> = ({ user, currentMoment }) => {
  const userMoment = currentMoment.tz(user.timezone);
  const userOffsetHoursStr = getTzOffsetString(userMoment);

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="sm">
        <HorizontalGroup justify="space-between">
          <Avatar src={user.avatar} size="large" />
        </HorizontalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{user.username}</Text>
          <Text type="secondary">
            {`${userMoment.tz(user.timezone).format('DD MMM, HH:mm')}`} {userOffsetHoursStr}
          </Text>
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );
};

export default ScheduleUserDetails;
