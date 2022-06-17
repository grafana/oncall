import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { HorizontalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import ScheduleUserDetails from 'components/ScheduleUserDetails/ScheduleUserDetails';
import Text from 'components/Text/Text';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';

import styles from './UsersTimezones.module.css';

interface UsersTimezonesProps {
  users: User[];
  tz: Timezone;
  onTzChange: (tz: Timezone) => void;
}

const cx = cn.bind(styles);

const hoursToSplit = 3;

const jLimit = 24 / hoursToSplit;

const UsersTimezones: FC<UsersTimezonesProps> = (props) => {
  const { users, tz, onTzChange } = props;

  const [count, setCount] = useState<number>(0);
  const [currentMoment, setCurrentMoment] = useState<dayjs.Dayjs>(dayjs().tz(tz).startOf('minute'));

  const getAvatarClickHandler = useCallback((user) => {
    return () => {
      onTzChange(user.tz);
    };
  }, []);

  useEffect(() => {
    setCurrentMoment(currentMoment.tz(tz).startOf('minute'));
  }, [tz]);

  /*useInterval(
    () => {
      setCurrentMoment(currentMoment.add(10, 'minute'));
      //setCount(count + 1);
    },
    // Delay in milliseconds or null to stop it
    1000,
  );*/

  const currentTimeX = useMemo(() => {
    const midnight = dayjs().tz(tz).startOf('day');
    const diff = currentMoment.diff(midnight, 'minutes');

    return (diff / 1440) * 100;
  }, [currentMoment, tz]);

  const momentsToRender = useMemo(() => {
    const momentsToRender = [];

    const d = dayjs().utc().startOf('day');

    for (let j = 0; j < jLimit; j++) {
      const m = dayjs(d).add(j * hoursToSplit, 'hour');
      momentsToRender.push(m);
    }
    return momentsToRender;
  }, []);

  return (
    <div className={cx('root')}>
      <div className={cx('header')}>
        <HorizontalGroup justify="space-between">
          <div className={cx('title')}>Daily team timezones</div>
          <div className={cx('timezone-select')}>
            <Text type="secondary">
              Current timezone: {tz}, local time: {currentMoment.format('HH:mm')}
            </Text>
          </div>
        </HorizontalGroup>
      </div>
      <div className={cx('users')}>
        <div className={cx('current-time')} style={{ left: `${currentTimeX}%` }} />
        {users.map((user, index) => {
          const userCurrentMoment = dayjs(currentMoment).tz(user.tz);
          const diff = userCurrentMoment.diff(userCurrentMoment.startOf('day'), 'minutes');

          const userHour = userCurrentMoment.hour();

          const x = (diff / 1440) * 100;
          return (
            <Tooltip
              interactive
              key={index}
              content={<ScheduleUserDetails currentMoment={currentMoment} user={user} />}
            >
              <div
                className={cx('user')}
                onClick={getAvatarClickHandler(user)}
                style={{
                  left: `${x}%`,
                  opacity: userHour >= 9 && userHour < 18 ? 1 : 0.5,
                }}
              >
                <Avatar src={user.avatar} size="large" />
              </div>
            </Tooltip>
          );
        })}
      </div>
      <div className={cx('time-stripe')}>
        <div className={cx('current-user-stripe')} />
        <div className={cx('time-marks')}>
          {momentsToRender.map((mm, index) => (
            <div key={index} className={cx('time-mark')} style={{ width: `${100 / jLimit}%` }}>
              <span
                className={cx('time-mark-text', {
                  'time-mark-text__translated': index > 0,
                })}
              >
                {mm.format('HH:mm')}
              </span>
            </div>
          ))}
          <div key={jLimit} className={cx('time-mark')}>
            <span className={cx('time-mark-text')}>24:00</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsersTimezones;
