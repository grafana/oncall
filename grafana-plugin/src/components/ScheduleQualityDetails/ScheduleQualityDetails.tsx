import React, { FC, useCallback, useEffect, useState } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import { ScheduleScoreQualityResponse, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';

import Text, { TextType } from 'components/Text/Text';

import styles from './ScheduleQualityDetails.module.scss';
import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

const cx = cn.bind(styles);

interface ScheduleQualityDetailsProps {
  quality: ScheduleScoreQualityResponse;
}

export const ScheduleQualityDetails: FC<ScheduleQualityDetailsProps> = ({ quality }) => {
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

  return (
    <div className={cx('root')}>
      <VerticalGroup>
        <Text type="secondary">
          Schedule quality:{' '}
          <Text type={getScheduleQualityMatchingColor(score)}>{getScheduleQualityFromNumber(score)}</Text>
        </Text>
        <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        <VerticalGroup>
          {comments?.length > 0 && (
            <div className={cx('row')}>
              <HorizontalGroup spacing="sm">
                <Icon name="calendar-alt" />
                <Text type="secondary">Rotation structure issues</Text>
              </HorizontalGroup>
              <div className={cx('indent-left')}>
                {comments.map((comment) => (
                  <Text type="primary">{comment}</Text>
                ))}
              </div>
            </div>
          )}

          {overloadedUsers?.length > 0 && (
            <div className={cx('row')}>
              <HorizontalGroup spacing="sm">
                <Icon name="users-alt" />
                <Text type="secondary">Overloaded users</Text>
              </HorizontalGroup>
              <div className={cx('indent-left')}>
                {overloadedUsers.map((overloadedUser) => (
                  <Text type="primary" className={cx('email')}>
                    {overloadedUser.email}
                  </Text>
                ))}
              </div>
            </div>
          )}
        </VerticalGroup>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Icon name="info-circle" />
              <Text type="secondary">Calculation methodology</Text>
            </HorizontalGroup>
            <IconButton name="angle-down" onClick={handleExpandClick} />
          </HorizontalGroup>
          {expanded && (
            <Text type="primary" className={cx('text')}>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer elementum purus egestas porta ultricies.
              Sed quis maximus sem. Phasellus semper pulvinar sapien ac euismod.
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

    const apiResponse = await userStore.getAll();
    const allUsersList: User[] = apiResponse.results;
    const overloadedUsers = [];

    allUsersList.forEach((user) => {
      if (overloaded_users.indexOf(user['pk']) !== -1) {
        overloadedUsers.push(user);
      }
    });

    setIsLoading(false);
    setOverloadedUsers(overloadedUsers);
  }

  function getScheduleQualityFromNumber(score: number): ScheduleScoreQualityResult {
    if (score < 20) return ScheduleScoreQualityResult.Bad;
    if (score < 40) return ScheduleScoreQualityResult.Low;
    if (score < 60) return ScheduleScoreQualityResult.Medium;
    if (score < 80) return ScheduleScoreQualityResult.Good;
    return ScheduleScoreQualityResult.Great;
  }

  function getScheduleQualityMatchingColor(score: number): TextType {
    if (score < 20) return 'danger';
    if (score < 60) return 'warning';
    return 'success';
  }
};
