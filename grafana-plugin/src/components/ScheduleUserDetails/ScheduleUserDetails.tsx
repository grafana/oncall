import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { isInWorkingHours } from 'components/WorkingHours/WorkingHours.helpers';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

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
  const isInWH = isInWorkingHours(currentMoment, user.working_hours, user.timezone);

  const store = useStore();

  const { teamStore } = store;
  let slackWorkspaceNameOrigin = teamStore.currentTeam.slack_team_identity.cached_name;
  const slackWorkspaceName = slackWorkspaceNameOrigin.replace(/[^0-9a-z]/gi, '');
  return (
    <div className={cx('root')}>
      <VerticalGroup spacing="md">
        <HorizontalGroup justify="space-between">
          <Avatar src={user.avatar} size="large" />
        </HorizontalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{user.username}</Text>
          {isOncall && <Badge text="OnCall now" color="green" />}
          {isInWH ? (
            <Badge text="Inside working hours" color="blue" />
          ) : (
            <Badge text="Outside working hours" color="orange" />
          )}
          <HorizontalGroup align="flex-start">
            <div className={cx('timezone-icon')}>
              <Text type="secondary">
                <Icon name="clock-nine" />
              </Text>
            </div>
            <div className={cx('timezone-wrapper')}>
              <div className={cx('timezone-info')}>
                <VerticalGroup>
                  <Text type="secondary">Local time</Text>
                  <Text type="secondary">{currentMoment.tz().format('DD MMM, HH:mm')}</Text>
                  <Text type="secondary">({getTzOffsetString(currentMoment)})</Text>
                </VerticalGroup>
              </div>

              <div className={cx('timezone-info')}>
                <VerticalGroup className={cx('timezone-info')}>
                  <Text>{user.username}'s time</Text>
                  <Text>{`${userMoment.tz(user.timezone).format('DD MMM, HH:mm')}`}</Text>
                  <Text>({userOffsetHoursStr})</Text>
                </VerticalGroup>
              </div>
            </div>
          </HorizontalGroup>
        </VerticalGroup>

        <hr className={cx('line-break')} />
        <VerticalGroup spacing="sm">
          <Text>Contacts</Text>

          <div className={cx('contact-details')}>
            <Text type="secondary">
              <Icon name="envelope" />{' '}
              <a href={`mailto:${user.email}`} target="_blank" rel="noreferrer">
                <Text type="link">{user.email}</Text>
              </a>{' '}
            </Text>
          </div>
          {user.slack_user_identity && (
            <div className={cx('contact-details')}>
              <Text type="secondary">
                <Icon name="slack" />{' '}
                <a
                  href={`https://${slackWorkspaceName}.slack.com/team/${user.slack_user_identity.slack_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Text type="link">{user.slack_user_identity.slack_login}</Text>
                </a>{' '}
              </Text>
            </div>
          )}
          {user.telegram_configuration && (
            <div className={cx('contact-details')}>
              <Text type="secondary">
                <Icon name="message" />{' '}
                <a
                  href={`https://t.me/${user.telegram_configuration.telegram_nick_name}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Text type="link">{user.telegram_configuration.telegram_nick_name}</Text>
                </a>{' '}
              </Text>
            </div>
          )}
          {!user.hide_phone_number && user.verified_phone_number && (
            <Text type="secondary">Phone: {user.verified_phone_number}</Text>
          )}
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );
};

export default ScheduleUserDetails;
