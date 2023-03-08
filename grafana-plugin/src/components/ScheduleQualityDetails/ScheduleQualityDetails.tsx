import React, { FC, useCallback, useEffect, useState } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text, { TextType } from 'components/Text/Text';
import { ScheduleScoreQualityResponse, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './ScheduleQualityDetails.module.scss';
import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';

const cx = cn.bind(styles);

interface ScheduleQualityDetailsProps {
  quality: ScheduleScoreQualityResponse;
  getScheduleQualityString: (score: number) => ScheduleScoreQualityResult;
}

export const ScheduleQualityDetails: FC<ScheduleQualityDetailsProps> = ({ quality, getScheduleQualityString }) => {
  const { userStore } = useStore();
  const { total_score: score, comments, overloaded_users } = quality;
  const [expanded, setExpanded] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [overloadedUsers, setOverloadedUsers] = useState<User[]>([]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleExpandClick = useCallback(() => {
    setExpanded((expanded) => !expanded);
  }, []);

  if (isLoading) {
    return null;
  }

  const infoComments = comments.filter((c) => c.type === 'info');
  const warningComments = comments.filter((c) => c.type === 'warning');

  return (
    <div className={cx('root')}>
      <VerticalGroup>
        <Text type="secondary">
          Schedule quality: <Text type={getScheduleQualityMatchingColor(score)}>{getScheduleQualityString(score)}</Text>
        </Text>
        <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        <VerticalGroup>
          {comments?.length > 0 && (
            <VerticalGroup spacing="sm" className={cx('row')}>
              {/* Show Info comments */}
              {infoComments?.length > 0 && (
                <div className={cx('row')}>
                  <HorizontalGroup spacing="sm" align="flex-start">
                    <Icon name="info-circle" />
                    <VerticalGroup spacing="none" className={cx('indent-left')}>
                      {infoComments.map((comment, index) => (
                        <Text type="primary" key={index}>
                          {comment.text}
                        </Text>
                      ))}
                    </VerticalGroup>
                  </HorizontalGroup>
                </div>
              )}

              {/* Show Warning comments afterwards */}
              {warningComments?.length > 0 && (
                <div className={cx('row')}>
                  <HorizontalGroup spacing="sm">
                    <Icon name="calendar-alt" />
                    <Text type="secondary">Rotation structure issues</Text>
                  </HorizontalGroup>

                  <div className={cx('indent-left')}>
                    {warningComments.map((comment, index) => (
                      <Text type="primary" key={index}>
                        {comment.text}
                      </Text>
                    ))}
                  </div>
                </div>
              )}
            </VerticalGroup>
          )}

          {overloadedUsers?.length > 0 && (
            <div className={cx('row')}>
              <HorizontalGroup spacing="sm">
                <Icon name="users-alt" />
                <Text type="secondary">Overloaded users</Text>
              </HorizontalGroup>
              <div className={cx('indent-left')}>
                {overloadedUsers.map((overloadedUser, index) => (
                  <Text type="primary" className={cx('email')} key={index}>
                    {overloadedUser.email} ({getTzOffsetString(dayjs().tz(overloadedUser.timezone))})
                  </Text>
                ))}
              </div>
            </div>
          )}
        </VerticalGroup>

        <div className={cx('line-break')} />

        <VerticalGroup spacing="xs">
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Icon name="calculator-alt" />
              <Text type="secondary">Calculation methodology</Text>
            </HorizontalGroup>
            <IconButton name={expanded ? 'arrow-down' : 'arrow-right'} onClick={handleExpandClick} />
          </HorizontalGroup>
          {expanded && (
            <Text type="primary" className={cx('text')}>
              The latest 90 days are taken into consideration when calculating the overall schedule quality.
            </Text>
          )}
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );

  async function fetchUsers() {
    if (!overloaded_users?.length) {
      setIsLoading(false);
      return;
    }

    const allUsersList: User[] = userStore.getSearchResult().results;
    const overloadedUsers = [];

    allUsersList.forEach((user) => {
      if (overloaded_users.indexOf(user['pk']) !== -1) {
        overloadedUsers.push(user);
      }
    });

    setIsLoading(false);
    setOverloadedUsers(overloadedUsers);
  }

  function getScheduleQualityMatchingColor(score: number): TextType {
    if (score < 20) {
      return 'danger';
    }
    if (score < 60) {
      return 'warning';
    }
    return 'success';
  }
};
