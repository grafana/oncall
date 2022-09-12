import React, { FC } from 'react';

import { Icon, Button, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';

import Line from './img/line.svg';

import styles from './ScheduleUserDetails.module.css';

interface ScheduleUserDetailsProps {
  currentMoment: dayjs.Dayjs;
  user: User;
}

const cx = cn.bind(styles);

enum UserOncallStatus {
  Now = 'now',
  Outside = 'outside',
  Inside = 'inside',
}

const userOncallStatusToText = {
  [UserOncallStatus.Now]: 'Oncall now',
  [UserOncallStatus.Inside]: 'Inside working hours',
  [UserOncallStatus.Outside]: 'Outside working hours',
};

const ScheduleUserDetails: FC<ScheduleUserDetailsProps> = (props) => {
  const { user, currentMoment } = props;

  const userStatus =
    Math.random() > 0.66
      ? UserOncallStatus.Now
      : Math.random() > 0.33
      ? UserOncallStatus.Inside
      : UserOncallStatus.Outside;

  const userMoment = currentMoment.tz(user.timezone);

  const userOffsetHoursStr = getTzOffsetString(userMoment);

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="sm">
        <HorizontalGroup justify="space-between">
          <Avatar src={user.avatar} size="large" />
          {/*<Button variant="secondary">
            <HorizontalGroup spacing="sm">
              <Icon name="bell" />
              Push
            </HorizontalGroup>
          </Button>*/}
        </HorizontalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{user.username}</Text>
          <Text type="secondary">
            {`${userMoment.tz(user.timezone).format('DD MMM, HH:mm')}`} {userOffsetHoursStr}
          </Text>
          {/* <div
            className={cx('oncall-badge', {
              [`oncall-badge__type_${userStatus}`]: true,
            })}
          >
            {userOncallStatusToText[userStatus]}
          </div>
          <HorizontalGroup>
            <VerticalGroup spacing="sm">
              <Text type="primary">Next shift</Text>
              <div className={cx('times')}>
                <HorizontalGroup>
                  <img src={Line} />
                  <VerticalGroup spacing="none">
                    <Text type="secondary">30 apr, 00:00</Text>
                    <Text type="secondary">30 apr, 23:59</Text>
                  </VerticalGroup>
                </HorizontalGroup>
              </div>
            </VerticalGroup>
            <VerticalGroup spacing="sm">
              <Text type="primary">Last shift</Text>
              <div className={cx('times')}>
                <HorizontalGroup>
                  <img src={Line} />
                  <VerticalGroup spacing="none">
                    <Text type="secondary">30 apr, 00:00</Text>
                    <Text type="secondary">30 apr, 23:59</Text>
                  </VerticalGroup>
                </HorizontalGroup>
              </div>
            </VerticalGroup>
          </HorizontalGroup>
        </VerticalGroup>
        <hr style={{ width: '100%' }} />
        <VerticalGroup spacing="sm">
          <Text type="primary">Contacts</Text>
          <HorizontalGroup spacing="sm">
            <Icon className={cx('icon')} name="message" />
            <Text type="link">mail@grafana.com</Text>
          </HorizontalGroup>
          <HorizontalGroup spacing="sm">
            <Icon className={cx('icon')} name="slack" />
            <Text type="link">@slackid</Text>
          </HorizontalGroup>
          <HorizontalGroup spacing="sm">
            <Icon className={cx('icon')} name="phone" />
            <Text type="secondary">+39 555 449 00 00</Text>
          </HorizontalGroup>*/}
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );
};

export default ScheduleUserDetails;
