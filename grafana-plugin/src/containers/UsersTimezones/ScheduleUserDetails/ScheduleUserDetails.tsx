import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Stack, Icon, Badge, useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { isUserActionAllowed, UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Avatar } from 'components/Avatar/Avatar';
import { ScheduleBorderedAvatar } from 'components/ScheduleBorderedAvatar/ScheduleBorderedAvatar';
import { Text } from 'components/Text/Text';
import { isInWorkingHours } from 'components/WorkingHours/WorkingHours.helpers';
import {
  getCurrentDateInTimezone,
  getCurrentlyLoggedInUserDate,
  getTzOffsetString,
} from 'models/timezone/timezone.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getColorSchemeMappingForUsers } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

interface ScheduleUserDetailsProps {
  currentMoment: dayjs.Dayjs;
  user: ApiSchemas['User'];
  isOncall: boolean;
  scheduleId: string;
}

export const ScheduleUserDetails: FC<ScheduleUserDetailsProps> = observer((props) => {
  const {
    timezoneStore: { calendarStartDate },
  } = useStore();
  const { user, currentMoment, isOncall, scheduleId } = props;
  const isInWH = isInWorkingHours(currentMoment, user.working_hours, user.timezone);

  const store = useStore();
  const colorSchemeMapping = getColorSchemeMappingForUsers(store, scheduleId, calendarStartDate);
  const colorSchemeList = Array.from(colorSchemeMapping[user.pk] || []);

  const { organizationStore } = store;
  const slackWorkspaceName =
    organizationStore.currentOrganization?.slack_team_identity?.cached_name?.replace(/[^0-9a-z]/gi, '') || '';

  const styles = useStyles2(getStyles);

  return (
    <div className={styles.root} data-testid="schedule-user-details">
      <Stack direction="column" gap={StackSize.xs}>
        <ScheduleBorderedAvatar
          colors={colorSchemeList}
          width={35}
          height={35}
          renderAvatar={() => <Avatar src={user.avatar} size="large" />}
          renderIcon={() => null}
        />

        <Stack direction="column" gap={StackSize.xs} width="100%">
          <div className={styles.username}>
            <Text type="primary">{user.username}</Text>
          </div>
          <Stack gap={StackSize.xs}>
            {isOncall && <Badge text="On-call" color="green" />}
            {isInWH ? (
              <Badge text="Inside working hours" color="blue" />
            ) : (
              <Badge text="Outside working hours" color="orange" />
            )}
          </Stack>
          <div className={styles.userTimezones}>
            <div className={styles.timezoneIcon}>
              <Text type="secondary">
                <Icon name="clock-nine" />
              </Text>
            </div>
            <div className={styles.timezoneWrapper}>
              <div className={styles.timezoneInfo} data-testid="schedule-user-details_your-current-time">
                <Stack direction="column" gap={StackSize.none}>
                  <Text type="secondary">Your current time</Text>
                  <Text type="secondary">{getCurrentlyLoggedInUserDate().format('DD MMM, HH:mm')}</Text>
                  <Text type="secondary">({getTzOffsetString(getCurrentlyLoggedInUserDate())})</Text>
                </Stack>
              </div>

              <div className={styles.timezoneInfo} data-testid="schedule-user-details_user-local-time">
                <Stack direction="column" gap={StackSize.none}>
                  <Text>User's local time</Text>
                  <Text>{`${getCurrentDateInTimezone(user.timezone).format('DD MMM, HH:mm')}`}</Text>
                  <Text>({user.timezone})</Text>
                </Stack>
              </div>
            </div>
          </div>
        </Stack>

        {isUserActionAllowed(UserActions.UserSettingsAdmin) && (
          <Stack direction="column" gap={StackSize.xs}>
            <hr className={styles.lineBreak} />
            <Stack direction="column" gap={StackSize.xs}>
              <Text>Contacts</Text>

              <div className={styles.contactDetails}>
                <Text type="secondary">
                  <Icon name="envelope" className={cx('contact-icon')} />
                </Text>
                <a href={`mailto:${user.email}`} target="_blank" rel="noreferrer">
                  <Text type="link">{user.email}</Text>
                </a>
              </div>
              {user.slack_user_identity && (
                <div className={styles.contactDetails}>
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
                <div className={styles.contactDetails}>
                  <Text type="secondary">
                    <Icon name="message" className={styles.contactIcon} />
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
                <div className={styles.contactDetails}>
                  <Text type="secondary">
                    <Icon name="document-info" className={styles.contactIcon} />
                  </Text>
                  <Text type="secondary">{user.verified_phone_number}</Text>
                </div>
              )}
            </Stack>
          </Stack>
        )}
      </Stack>
    </div>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      width: 260px;
      padding: 8px 4px;
    `,

    oncallBadge: css`
      line-height: 16px;
      color: ${theme.colors.background.primary};
      padding: 2px 7px;
      border-radius: 4px;
      margin-bottom: 10px;
    `,

    oncallBadgeNow: css`
      background: #6ccf8e;
    `,

    oncallBadgeInside: css`
      background: #ccccdc;
    `,

    oncallBadgeOutside: css`
      background: rgba(204, 204, 220, 0.4);
    `,

    lineBreak: css`
      width: 100vw;
      margin: 8px -14px 8px -14px;
    `,

    icon: css`
      color: #ccccdc;
    `,

    username: css`
      word-break: break-all;
    `,

    timezoneWrapper: css`
      display: flex;
      flex-grow: 1;
    `,

    timezoneIcon: css`
      margin-right: 8px;
    `,

    contactIcon: css`
      margin-right: 8px;
    `,

    timezoneInfo: css`
      width: 50%;
      overflow-wrap: anywhere;
      margin-right: 8px;
    `,

    contactDetails: css`
      display: flex;

      a {
        text-decoration-line: none;
        word-break: break-all;
      }
    `,

    userTimezones: css`
      margin-top: 4px;
      display: flex;
      width: 100%;
    `,
  };
};
