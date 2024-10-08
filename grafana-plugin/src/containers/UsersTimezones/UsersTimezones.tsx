import React, { FC, useEffect, useMemo, useState } from 'react';

import { cx } from '@emotion/css';
import { Icon, Stack, Tooltip, useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { sortBy } from 'lodash-es';
import { observer } from 'mobx-react';

import { Avatar } from 'components/Avatar/Avatar';
import { ScheduleBorderedAvatar } from 'components/ScheduleBorderedAvatar/ScheduleBorderedAvatar';
import { Text } from 'components/Text/Text';
import { WorkingHours } from 'components/WorkingHours/WorkingHours';
import { IsOncallIcon } from 'icons/Icons';
import { Schedule } from 'models/schedule/schedule.types';
import { getCurrentDateInTimezone } from 'models/timezone/timezone.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getColorSchemeMappingForUsers } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

import { ScheduleUserDetails } from './ScheduleUserDetails/ScheduleUserDetails';
import { getUserTimezonesStyles } from './UserTimezones.styles';
import { calculateTimePassedInDayPercentage } from './UsersTimezones.helpers';

interface UsersTimezonesProps {
  userIds: Array<ApiSchemas['User']['pk']>;
  onCallNow: Array<Partial<ApiSchemas['User']>>;
  scheduleId: Schedule['id'];
}

const hoursToSplit = 3;

const jLimit = 24 / hoursToSplit;

export const UsersTimezones: FC<UsersTimezonesProps> = observer((props) => {
  const store = useStore();
  const {
    userStore,
    timezoneStore: { selectedTimezoneLabel, currentDateInSelectedTimezone },
  } = store;

  const { userIds, onCallNow, scheduleId } = props;
  const styles = useStyles2(getUserTimezonesStyles);

  useEffect(() => {
    userIds.forEach((userId) => {
      if (!store.userStore.items[userId]) {
        store.userStore.fetchItemById({ userPk: userId, skipIfAlreadyPending: true });
      }
    });
  }, [userIds]);

  const users = useMemo(
    () => userIds.map((userId) => store.userStore.items[userId]).filter(Boolean),
    [userIds, store.userStore.items]
  );

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
    <div className={styles.root}>
      <WorkingHours
        light
        startMoment={currentDateInSelectedTimezone.startOf('day')}
        duration={24 * 60 * 60}
        timezone={userStore.currentUser?.timezone}
        workingHours={userStore.currentUser?.working_hours}
        className={styles.workingHours}
      />
      <div className={styles.content}>
        <div className={styles.header}>
          <Stack justifyContent="space-between">
            <Stack>
              <div className={styles.title}>
                <Text.Title level={5} type="primary">
                  Schedule team and timezones
                </Text.Title>
              </div>
            </Stack>
            <div>
              <Text type="secondary">
                Current timezone: {selectedTimezoneLabel}, local time: {currentDateInSelectedTimezone.format('HH:mm')}
              </Text>
            </div>
          </Stack>
        </div>
        <div className={styles.users}>
          <CurrentTimeLineIndicator />
          {users?.length ? (
            <UserAvatars
              users={users}
              onCallNow={onCallNow}
              currentMoment={currentDateInSelectedTimezone}
              scheduleId={scheduleId}
            />
          ) : (
            <Stack justifyContent="center" alignItems="flex-start">
              <Stack>
                <Icon className={styles.icon} name="users-alt" />
                <Text type="secondary">Add rotation to see users</Text>
              </Stack>
            </Stack>
          )}
        </div>
        <div className={styles.timeMarksWrapper}>
          <div className={styles.timeMarks}>
            {momentsToRender.map((mm, index) => (
              <div key={index} className={styles.timeMark} style={{ width: `${100 / jLimit}%` }}>
                <span
                  className={cx(styles.timeMarkText, {
                    [styles.timeMarkTextTranslated]: index > 0,
                  })}
                >
                  <Text type="secondary" size="small">
                    {mm.format('HH:mm')}
                  </Text>
                </span>
              </div>
            ))}
            <div key={jLimit} className={styles.timeMark}>
              <span className={styles.timeMarkText}>
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
});

const CurrentTimeLineIndicator = observer(() => {
  const {
    timezoneStore: { currentDateInSelectedTimezone },
  } = useStore();
  const styles = useStyles2(getUserTimezonesStyles);

  return (
    <div
      className={styles.currentTime}
      style={{ left: `${calculateTimePassedInDayPercentage(currentDateInSelectedTimezone)}%` }}
    />
  );
});

interface UserAvatarsProps {
  users: Array<ApiSchemas['User']>;
  currentMoment: dayjs.Dayjs;
  scheduleId: Schedule['id'];
  onCallNow: Array<Partial<ApiSchemas['User']>>;
}

const UserAvatars = (props: UserAvatarsProps) => {
  const { users, currentMoment, onCallNow, scheduleId } = props;
  const userGroups = useMemo(
    () =>
      sortBy(
        users.reduce((memo, user) => {
          const userUtcOffset = dayjs().tz(user.timezone).utcOffset();
          let group = memo.find((group) => group.utcOffset === userUtcOffset);
          if (!group) {
            group = { utcOffset: userUtcOffset, users: [] };
            memo.push(group);
          }
          group.users.push(user);

          return memo;
        }, []),
        ({ utcOffset }) => utcOffset
      ),
    [users]
  );

  const [activeUtcOffset, setActiveUtcOffset] = useState<number | undefined>(undefined);

  return (
    <div>
      {userGroups.map((group, idx) => (
        <AvatarGroup
          key={idx}
          activeUtcOffset={activeUtcOffset}
          utcOffset={group.utcOffset}
          onSetActiveUtcOffset={setActiveUtcOffset}
          xPos={calculateTimePassedInDayPercentage(getCurrentDateInTimezone(group.users[0].timezone))}
          users={group.users}
          currentMoment={currentMoment}
          scheduleId={scheduleId}
          onCallNow={onCallNow}
        />
      ))}
    </div>
  );
};

interface AvatarGroupProps {
  users: Array<ApiSchemas['User']>;
  xPos: number;
  currentMoment: dayjs.Dayjs;
  utcOffset: number;
  scheduleId: Schedule['id'];
  onSetActiveUtcOffset: (utcOffset: number | undefined) => void;
  activeUtcOffset: number;
  onCallNow: Array<Partial<ApiSchemas['User']>>;
}

const LIMIT = 3;
const AVATAR_WIDTH = 32;
const AVATAR_GAP = 5;

const AvatarGroup = observer((props: AvatarGroupProps) => {
  const {
    users: propsUsers,
    currentMoment,
    xPos,
    utcOffset,
    onSetActiveUtcOffset,
    activeUtcOffset,
    onCallNow,
    scheduleId,
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

  const styles = useStyles2(getUserTimezonesStyles);
  const colorSchemeMapping = getColorSchemeMappingForUsers(store, scheduleId, store.timezoneStore.calendarStartDate);
  const width = active ? users.length * AVATAR_WIDTH + (users.length - 1) * AVATAR_GAP : AVATAR_WIDTH;

  return (
    <div
      className={cx(styles.avatarGroup, {
        [styles.avatarGroupInactive]: !isNaN(activeUtcOffset) && activeUtcOffset !== utcOffset,
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
              />
            }
          >
            <div
              className={styles.avatar}
              data-testid="user-avatar-in-schedule"
              style={{
                left: active ? `${index * (AVATAR_WIDTH + AVATAR_GAP)}px` : `${index * 10}px`,
                opacity: active ? 1 : Math.max(1 - index * 0.25, 0.25),
                visibility: !active && index >= LIMIT ? 'hidden' : 'visible',
                zIndex: array.length - index - 1,
              }}
            >
              <ScheduleBorderedAvatar
                colors={colorSchemeList}
                width={35}
                height={35}
                renderAvatar={() => <Avatar src={user.avatar} size="large" />}
                renderIcon={() =>
                  isOncall ? <IsOncallIcon className={styles.isOncallIcon} width={14} height={13} /> : null
                }
              />
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
        className={styles.userMore}
      >
        +{users.length - LIMIT}
      </div>
    </div>
  );
});
