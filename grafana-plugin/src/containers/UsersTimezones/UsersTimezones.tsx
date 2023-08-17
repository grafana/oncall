import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { HorizontalGroup, Icon, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import ScheduleBorderedAvatar from 'components/ScheduleBorderedAvatar/ScheduleBorderedAvatar';
import ScheduleUserDetails from 'components/ScheduleUserDetails/ScheduleUserDetails';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { IsOncallIcon } from 'icons';
import { Schedule } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getColorSchemeMappingForUsers } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

import styles from './UsersTimezones.module.css';

interface UsersTimezonesProps {
  userIds: Array<User['pk']>;
  tz: Timezone;
  onCallNow: Array<Partial<User>>;
  scheduleId: Schedule['id'];
  startMoment: dayjs.Dayjs;

  onTzChange: (tz: Timezone) => void;
}

const cx = cn.bind(styles);

const hoursToSplit = 3;

const jLimit = 24 / hoursToSplit;

const UsersTimezones: FC<UsersTimezonesProps> = (props) => {
  const store = useStore();
  const { userStore } = store;

  const { userIds, tz, onTzChange, onCallNow, scheduleId, startMoment } = props;

  useEffect(() => {
    userIds.forEach((userId) => {
      if (!store.userStore.items[userId]) {
        store.userStore.updateItem(userId);
      }
    });
  }, [userIds]);

  const users = useMemo(
    () => userIds.map((userId) => store.userStore.items[userId]).filter(Boolean),
    [userIds, store.userStore.items]
  );

  const currentMoment = useMemo(() => dayjs().tz(tz), [tz]);

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
      <WorkingHours
        light
        startMoment={currentMoment.startOf('day')}
        duration={24 * 60 * 60}
        timezone={userStore.currentUser?.timezone}
        workingHours={userStore.currentUser?.working_hours}
        className={cx('working-hours')}
      />
      {/*  <div className={cx('shades', 'shades--left')} />
      <div className={cx('shades', 'shades--right')} /> */}
      <div className={cx('content')}>
        <div className={cx('header')}>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup>
              <div className={cx('title')}>
                <Text.Title level={4} type="primary">
                  Schedule team and timezones
                </Text.Title>
              </div>
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
          {users && users.length ? (
            <UserAvatars
              users={users}
              onCallNow={onCallNow}
              onTzChange={onTzChange}
              currentMoment={currentMoment}
              startMoment={startMoment}
              scheduleId={scheduleId}
            />
          ) : (
            <HorizontalGroup justify="center" align="flex-start">
              <HorizontalGroup>
                <Icon className={cx('icon')} name="users-alt" />
                <Text type="secondary">Add rotation to see users</Text>
              </HorizontalGroup>
            </HorizontalGroup>
          )}
        </div>
        <div className={cx('time-marks-wrapper')}>
          <div className={cx('time-marks')}>
            {momentsToRender.map((mm, index) => (
              <div key={index} className={cx('time-mark')} style={{ width: `${100 / jLimit}%` }}>
                <span
                  className={cx('time-mark-text', {
                    'time-mark-text__translated': index > 0,
                  })}
                >
                  <Text type="secondary" size="small">
                    {mm.format('HH:mm')}
                  </Text>
                </span>
              </div>
            ))}
            <div key={jLimit} className={cx('time-mark')}>
              <span className={cx('time-mark-text')}>
                <Text type="secondary" size="small">
                  24:00
                </Text>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface UserAvatarsProps {
  users: User[];
  currentMoment: dayjs.Dayjs;
  startMoment: dayjs.Dayjs;
  scheduleId: Schedule['id'];
  onTzChange: (timezone: Timezone) => void;
  onCallNow: Array<Partial<User>>;
}

const UserAvatars = (props: UserAvatarsProps) => {
  const { users, currentMoment, onCallNow, scheduleId, startMoment } = props;
  const userGroups = useMemo(() => {
    return users
      .reduce((memo, user) => {
        const userUtcOffset = dayjs().tz(user.timezone).utcOffset();
        let group = memo.find((group) => group.utcOffset === userUtcOffset);
        if (!group) {
          group = { utcOffset: userUtcOffset, users: [] };
          memo.push(group);
        }
        group.users.push(user);

        return memo;
      }, [])
      .sort((a, b) => {
        if (a.utcOffset > b.utcOffset) {
          return 1;
        }
        if (a.utcOffset < b.utcOffset) {
          return -1;
        }

        return 0;
      });
  }, [users]);

  const [activeUtcOffset, setActiveUtcOffset] = useState<number | undefined>(undefined);

  return (
    <div className={cx('user-avatars')}>
      {userGroups.map((group, idx) => {
        const userCurrentMoment = dayjs(currentMoment).tz(group.users[0].timezone); // TODO try using group.utcOffset
        const diff = userCurrentMoment.diff(userCurrentMoment.startOf('day'), 'minutes');

        const xPos = (diff / (60 * 24)) * 100;

        return (
          <AvatarGroup
            key={idx}
            activeUtcOffset={activeUtcOffset}
            utcOffset={group.utcOffset}
            onSetActiveUtcOffset={setActiveUtcOffset}
            // onTzChange={onTzChange}
            xPos={xPos}
            users={group.users}
            startMoment={startMoment}
            currentMoment={currentMoment}
            scheduleId={scheduleId}
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
  startMoment: dayjs.Dayjs;
  currentMoment: dayjs.Dayjs;
  utcOffset: number;
  scheduleId: Schedule['id'];
  onSetActiveUtcOffset: (utcOffset: number | undefined) => void;
  activeUtcOffset: number;
  onTzChange?: (timezone: Timezone) => void;
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
    onTzChange,
    utcOffset,
    onSetActiveUtcOffset,
    activeUtcOffset,
    onCallNow,
    scheduleId,
    startMoment,
  } = props;

  const store = useStore();

  const active = !isNaN(activeUtcOffset) && activeUtcOffset === utcOffset;

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
  }, [propsUsers, onCallNow]);

  const getAvatarClickHandler = useCallback(
    (timezone: Timezone) => {
      return () => {
        onTzChange(timezone);
      };
    },
    [onTzChange]
  );

  const colorSchemeMapping = getColorSchemeMappingForUsers(store, scheduleId, startMoment);
  const width = active ? users.length * AVATAR_WIDTH + (users.length - 1) * AVATAR_GAP : AVATAR_WIDTH;

  return (
    <div
      className={cx('avatar-group', {
        [`avatar-group_inactive`]: !isNaN(activeUtcOffset) && activeUtcOffset !== utcOffset,
      })}
      style={{ width: `${width}px`, left: `${xPos}%`, transform: `translate(${translateLeft}px, 0)` }}
      onMouseEnter={() => onSetActiveUtcOffset(utcOffset)}
      onMouseLeave={() => onSetActiveUtcOffset(undefined)}
    >
      {users.map((user, index, array) => {
        const isOncall = onCallNow.some((onCallUser) => user.pk === onCallUser.pk);
        const colorSchemeList = colorSchemeMapping[user.pk] ? Array.from(colorSchemeMapping[user.pk]) : [];

        return (
          <Tooltip
            placement="top"
            interactive
            key={index}
            content={
              <ScheduleUserDetails
                currentMoment={currentMoment}
                user={user}
                isOncall={isOncall}
                scheduleId={scheduleId}
                startMoment={startMoment}
              />
            }
          >
            <div
              className={cx('avatar')}
              style={{
                left: active ? `${index * (AVATAR_WIDTH + AVATAR_GAP)}px` : `${index * 10}px`,
                opacity: active ? 1 : Math.max(1 - index * 0.25, 0.25),
                visibility: !active && index >= LIMIT ? 'hidden' : 'visible',
                zIndex: array.length - index - 1,
              }}
              onClick={getAvatarClickHandler(user.timezone)}
            >
              <ScheduleBorderedAvatar
                colors={colorSchemeList}
                width={35}
                height={35}
                renderAvatar={() => <Avatar src={user.avatar} size="large" />}
                renderIcon={() =>
                  isOncall ? <IsOncallIcon className={cx('is-oncall-icon')} width={14} height={13} /> : null
                }
              ></ScheduleBorderedAvatar>
            </div>
          </Tooltip>
        );
      })}
      <div
        style={{
          opacity: !active && users.length > LIMIT ? '1' : '0',
          zIndex: users.length,
          left: active ? `${users.length * (AVATAR_WIDTH + AVATAR_GAP)}px` : `${LIMIT * 10}px`,
        }}
        className={cx('user-more')}
      >
        +{users.length - LIMIT}
      </div>
    </div>
  );
};

export default UsersTimezones;
