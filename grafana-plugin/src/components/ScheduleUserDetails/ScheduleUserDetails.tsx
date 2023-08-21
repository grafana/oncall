import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import ScheduleBorderedAvatar from 'components/ScheduleBorderedAvatar/ScheduleBorderedAvatar';
import Text from 'components/Text/Text';
import { isInWorkingHours } from 'components/WorkingHours/WorkingHours.helpers';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { getColorSchemeMappingForUsers } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';

import styles from './ScheduleUserDetails.module.css';

interface ScheduleUserDetailsProps {
  currentMoment: dayjs.Dayjs;
  user: User;
  isOncall: boolean;
  scheduleId: string;
  startMoment: dayjs.Dayjs;
}

const cx = cn.bind(styles);

const ScheduleUserDetails: FC<ScheduleUserDetailsProps> = (props) => {
  const { user, currentMoment, isOncall, scheduleId, startMoment } = props;
  const userMoment = currentMoment.tz(user.timezone);
  const userOffsetHoursStr = getTzOffsetString(userMoment);
  const isInWH = isInWorkingHours(currentMoment, user.working_hours, user.timezone);

  const store = useStore();
  const colorSchemeMapping = getColorSchemeMappingForUsers(store, scheduleId, startMoment);
  const colorSchemeList = Array.from(colorSchemeMapping[user.pk] || []);

  const { organizationStore } = store;
  const slackWorkspaceName =
    organizationStore.currentOrganization.slack_team_identity?.cached_name?.replace(/[^0-9a-z]/gi, '') || '';

  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="xs">
        <ScheduleBorderedAvatar
          colors={colorSchemeList}
          width={35}
          height={35}
          renderAvatar={() => <Avatar src={user.avatar} size="large" />}
          renderIcon={() => null}
        ></ScheduleBorderedAvatar>

        <VerticalGroup spacing="xs" width="100%">
          <div className={cx('username')}>
            <Text type="primary">{user.username}</Text>
          </div>
          <HorizontalGroup spacing="xs">
            {isOncall && <Badge text="OnCall" color="green" />}
            {isInWH ? (
              <Badge text="Inside working hours" color="blue" />
            ) : (
              <Badge text="Outside working hours" color="orange" />
            )}
          </HorizontalGroup>
          <div className={cx('user-timezones')}>
            <div className={cx('timezone-icon')}>
              <Text type="secondary">
                <Icon name="clock-nine" />
              </Text>
            </div>
            <div className={cx('timezone-wrapper')}>
              <div className={cx('timezone-info')}>
                <VerticalGroup spacing="none">
                  <Text type="secondary">Local time</Text>
                  <Text type="secondary">{currentMoment.tz().format('DD MMM, HH:mm')}</Text>
                  <Text type="secondary">({getTzOffsetString(currentMoment)})</Text>
                </VerticalGroup>
              </div>

              <div className={cx('timezone-info')}>
                <VerticalGroup className={cx('timezone-info')} spacing="none">
                  <Text>User's time</Text>
                  <Text>{`${userMoment.tz(user.timezone).format('DD MMM, HH:mm')}`}</Text>
                  <Text>({userOffsetHoursStr})</Text>
                </VerticalGroup>
              </div>
            </div>
          </div>
        </VerticalGroup>

        {isUserActionAllowed(UserActions.UserSettingsAdmin) && (
          <VerticalGroup spacing="xs">
            <hr className={cx('line-break')} />
            <VerticalGroup spacing="xs">
              <Text>Contacts</Text>

              <div className={cx('contact-details')}>
                <Text type="secondary">
                  <Icon name="envelope" className={cx('contact-icon')} />
                </Text>
                <a href={`mailto:${user.email}`} target="_blank" rel="noreferrer">
                  <Text type="link">{user.email}</Text>
                </a>
              </div>
              {user.slack_user_identity && (
                <div className={cx('contact-details')}>
                  <Text type="secondary">
                    <Icon name="slack" className={cx('contact-icon')} />
                  </Text>
                  <a
                    href={`https://${slackWorkspaceName}.slack.com/team/${user.slack_user_identity.slack_id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Text type="link">{user.slack_user_identity.slack_login}</Text>
                  </a>
                </div>
              )}
              {user.telegram_configuration && (
                <div className={cx('contact-details')}>
                  <Text type="secondary">
                    <Icon name="message" className={cx('contact-icon')} />
                  </Text>
                  <a
                    href={`https://t.me/${user.telegram_configuration.telegram_nick_name}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Text type="link">{user.telegram_configuration.telegram_nick_name}</Text>
                  </a>
                </div>
              )}
              {!user.hide_phone_number && user.verified_phone_number && (
                <div className={cx('contact-details')}>
                  <Text type="secondary">
                    <Icon name="document-info" className={cx('contact-icon')} />
                  </Text>
                  <Text type="secondary">{user.verified_phone_number}</Text>
                </div>
              )}
            </VerticalGroup>
          </VerticalGroup>
        )}
      </VerticalGroup>
    </div>
  );
};

export default ScheduleUserDetails;
