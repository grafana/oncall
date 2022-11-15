import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { isInWorkingHours } from 'components/WorkingHours/WorkingHours.helpers';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';

import styles from './ScheduleUserDetails.module.css';

interface ScheduleUserDetailsProps {
  currentMoment: dayjs.Dayjs;
  user: User;
  isOncall: boolean;
}

const cx = cn.bind(styles);

const ScheduleUserDetails: FC<ScheduleUserDetailsProps> = (props) => {
  const { user, currentMoment, isOncall } = props;
  const userMoment = currentMoment.tz(user.timezone);
  const userOffsetHoursStr = getTzOffsetString(userMoment);

  console.log('USER', user);
  console.log('1', userMoment.weekday());
  console.log('2', userMoment.toDate());

  isInWorkingHours(userMoment, user.working_hours);
  // console.log('NON WORK HOURS', getNonWorkingMoments(u))
  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="sm">
        <HorizontalGroup justify="space-between">
          <Avatar src={user.avatar} size="large" />
        </HorizontalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{user.username}</Text>
          {isOncall && <Badge text="OnCall now" color="green" />}

          <HorizontalGroup>
            <Icon name="clock-nine" />
            <VerticalGroup>
              <Text type="secondary">Local time</Text>
              <Text type="secondary">{currentMoment.tz().format('DD MMM, HH:mm')}</Text>
              <Text type="secondary">({getTzOffsetString(currentMoment)})</Text>
            </VerticalGroup>
            <VerticalGroup>
              <Text>{user.username}'s time</Text>
              <Text>{`${userMoment.tz(user.timezone).format('DD MMM, HH:mm')}`}</Text>
              <Text>({userOffsetHoursStr})</Text>
            </VerticalGroup>
          </HorizontalGroup>
          <hr className={cx('hr')} />
          <Text>Contacts</Text>
          <Text>Email: {user.email}</Text>
          {user.slack_user_identity && <Text>Slack: {user.slack_user_identity.slack_login}</Text>}
          {user.telegram_configuration && <Text>Telegram: {user.telegram_configuration.telegram_nick_name}</Text>}
          {!user.hide_phone_number && user.verified_phone_number && <Text>Phone: {user.verified_phone_number}</Text>}
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );
};

export default ScheduleUserDetails;
