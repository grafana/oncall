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
      <div className={cx('container')}>
        <Text type="secondary">
          Schedule quality:{' '}
          <Text type={getScheduleQualityMatchingColor(score)} className={cx('semi-bold')}>
            {getScheduleQualityString(score)}
          </Text>
        </Text>
        <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        <div className={cx('container', 'container--withPadding')}>
          {comments?.length > 0 && (
            <VerticalGroup spacing="sm" className={cx('row')}>
              {/* Show Info comments */}
              {infoComments?.length > 0 && (
                <div className={cx('container')}>
                  <div className={cx('row')}>
                    <Icon name="info-circle" />
                    <div className={cx('container')}>
                      {infoComments.map((comment, index) => (
                        <Text type="primary" key={index}>
                          {comment.text}
                        </Text>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Show Warning comments afterwards */}
              {warningComments?.length > 0 && (
                <div className={cx('container')}>
                  <div className={cx('row')}>
                    <Icon name="calendar-alt" />
                    <div className={cx('container')}>
                      <Text type="secondary">Rotation structure issues</Text>
                      {warningComments.map((comment, index) => (
                        <Text type="primary" key={index}>
                          {comment.text}
                        </Text>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </VerticalGroup>
          )}

          {overloadedUsers?.length > 0 && (
            <div className={cx('container')}>
              <div className={cx('row')}>
                <Icon name="users-alt" />
                <div className={cx('container')}>
                  <Text type="secondary">Overloaded users</Text>
                  {overloadedUsers.map((overloadedUser, index) => (
                    <Text type="primary" className={cx('email')} key={index}>
                      {overloadedUser.email} ({getTzOffsetString(dayjs().tz(overloadedUser.timezone))})
                    </Text>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={cx('line-break')} />

        <div className={cx('container', 'container--withPadding')}>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Icon name="calculator-alt" />
              <Text type="secondary" className={cx('metholodogy')}>
                Calculation methodology
              </Text>
            </HorizontalGroup>
            <IconButton name={expanded ? 'arrow-down' : 'arrow-right'} onClick={handleExpandClick} />
          </HorizontalGroup>
          {expanded && (
            <Text type="primary" className={cx('text')}>
              The latest 90 days are taken into consideration when calculating the overall schedule quality.
            </Text>
          )}
        </div>
      </div>
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
