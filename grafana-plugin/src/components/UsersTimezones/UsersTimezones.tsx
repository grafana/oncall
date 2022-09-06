import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { HorizontalGroup, InlineSwitch, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import ScheduleUserDetails from 'components/ScheduleUserDetails/ScheduleUserDetails';
import Text from 'components/Text/Text';
import { IsOncallIcon } from 'icons';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';

import styles from './UsersTimezones.module.css';

interface UsersTimezonesProps {
  users: User[];
  tz: Timezone;
  onTzChange: (tz: Timezone) => void;
  onCallNow: Array<Partial<User>>;
}

const cx = cn.bind(styles);

const hoursToSplit = 3;

const jLimit = 24 / hoursToSplit;

const UsersTimezones: FC<UsersTimezonesProps> = (props) => {
  const { users, tz, onTzChange, onCallNow } = props;

  const [count, setCount] = useState<number>(0);
  const [currentMoment, setCurrentMoment] = useState<dayjs.Dayjs>(dayjs().tz(tz));

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
          <HorizontalGroup>
            <div className={cx('title')}>Schedule team and timezones</div>
            {/* <HorizontalGroup>
              <InlineSwitch transparent />
              Current schedule users only
            </HorizontalGroup>*/}
          </HorizontalGroup>
          <div className={cx('timezone-select')}>
            <Text type="secondary">
              Current timezone: {tz}, local time: {currentMoment.format('HH:mm')}
            </Text>
          </div>
        </HorizontalGroup>
      </div>
      <div className={cx('users')}>
        <div className={cx('current-time')} style={{ left: `${currentTimeX}%` }} />
        <UserAvatars users={users} onCallNow={onCallNow} onTzChange={onTzChange} currentMoment={currentMoment} />
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

interface UserAvatarsProps {
  users: User[];
  currentMoment: dayjs.Dayjs;
  onTzChange: (timezone: Timezone) => void;
  onCallNow: Array<Partial<User>>;
}

const UserAvatars = (props: UserAvatarsProps) => {
  const { users, currentMoment, onTzChange, onCallNow } = props;
  const userGroups = useMemo(() => {
    return users
      .reduce((memo, user) => {
        let group = memo.find((group) => group.timezone === user.timezone);
        if (!group) {
          group = { timezone: user.timezone, users: [] };
          memo.push(group);
        }
        group.users.push(user);

        return memo;
      }, [])
      .sort((a, b) => {
        const aOffset = dayjs().tz(a.timezone).utcOffset();
        const bOffset = dayjs().tz(b.timezone).utcOffset();

        if (aOffset > bOffset) {
          return 1;
        }
        if (aOffset < bOffset) {
          return -1;
        }

        return 0;
      });
  }, [users]);

  const getAvatarClickHandler = useCallback((timezone: Timezone) => {
    return () => {
      onTzChange(timezone);
    };
  }, []);

  const [activeTimezone, setActiveTimezone] = useState<Timezone | undefined>(undefined);

  return (
    <div className={cx('user-avatars')}>
      {userGroups.map((group) => {
        const userCurrentMoment = dayjs(currentMoment).tz(group.timezone);
        const diff = userCurrentMoment.diff(userCurrentMoment.startOf('day'), 'minutes');

        const xPos = (diff / (60 * 24)) * 100;

        return (
          <AvatarGroup
            activeTimezone={activeTimezone}
            timezone={group.timezone}
            onSetActiveTimezone={setActiveTimezone}
            onClick={getAvatarClickHandler(group.timezone)}
            xPos={xPos}
            users={group.users}
            currentMoment={currentMoment}
            onCallNow={onCallNow}
          />
        );
      })}
    </div>
  );
};

interface AvatarGroupProps {
  users: User[];
  xPos: number;
  currentMoment: dayjs.Dayjs;
  onClick: () => void;
  timezone: Timezone;
  onSetActiveTimezone: (timezone: Timezone) => void;
  activeTimezone: Timezone;
  onCallNow: Array<Partial<User>>;
}

const LIMIT = 3;
const AVATAR_WIDTH = 32;
const AVATAR_GAP = 5;

const AvatarGroup = (props: AvatarGroupProps) => {
  const {
    users: propsUsers,
    currentMoment,
    xPos,
    onClick,
    timezone,
    onSetActiveTimezone,
    activeTimezone,
    onCallNow,
  } = props;

  const active = activeTimezone && activeTimezone === timezone;

  const translateLeft = -AVATAR_WIDTH / 2;

  const users = useMemo(() => {
    return [...propsUsers].sort((a, b) => {
      const aIsOncall = Number(onCallNow.some((onCallUser) => a.pk === onCallUser.pk));
      const bIsOncall = Number(onCallNow.some((onCallUser) => b.pk === onCallUser.pk));

      if (aIsOncall < bIsOncall) {
        return 1;
      }
      if (aIsOncall > bIsOncall) {
        return -1;
      }

      return 0;
    });
  }, [propsUsers]);

  const width = active ? users.length * AVATAR_WIDTH + (users.length - 1) * AVATAR_GAP : AVATAR_WIDTH;

  return (
    <div
      className={cx('avatar-group', { [`avatar-group_inactive`]: activeTimezone && activeTimezone !== timezone })}
      style={{ width: `${width + AVATAR_GAP}px`, left: `${xPos}%`, transform: `translate(${translateLeft}px, 0)` }}
      onClick={onClick}
      onMouseEnter={() => onSetActiveTimezone(timezone)}
      onMouseLeave={() => onSetActiveTimezone(undefined)}
    >
      {users.map((user, index, array) => {
        const isOncall = onCallNow.some((onCallUser) => user.pk === onCallUser.pk);

        return (
          <Tooltip
            placement="top"
            interactive
            key={index}
            content={<ScheduleUserDetails currentMoment={currentMoment} user={user} />}
          >
            <div
              className={cx('avatar')}
              style={{
                left: active ? `${index * (AVATAR_WIDTH + AVATAR_GAP)}px` : `${index * 10}px`,
                opacity: active ? 1 : Math.max(1 - index * 0.25, 0.25),
                visibility: !active && index >= LIMIT ? 'hidden' : 'visible',
                zIndex: array.length - index - 1,
                /* opacity: userHour >= 9 && userHour < 18 ? 1 : 0.5,*/
              }}
            >
              <Avatar src={user.avatar} size="large" />
              {isOncall && <IsOncallIcon className={cx('is-oncall-icon')} />}
            </div>
          </Tooltip>
        );
      })}
      <div
        style={{
          opacity: !active && users.length > LIMIT ? '1' : '0',
          zIndex: users.length,
          left: active ? `${users.length * (AVATAR_WIDTH + AVATAR_GAP)}px` : `${users.length * 10}px`,
        }}
        className={cx('user-more')}
      >
        +{users.length - LIMIT}
      </div>
    </div>
  );
};

export default UsersTimezones;
