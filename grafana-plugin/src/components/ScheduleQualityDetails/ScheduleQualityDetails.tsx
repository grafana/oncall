import React, { FC, useCallback, useState } from 'react';

import { HorizontalGroup, Icon, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { ScheduleScoreQualityResponse, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';
import { getVar } from 'utils/DOM';

import styles from './ScheduleQualityDetails.module.scss';
import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';

const cx = cn.bind(styles);

interface ScheduleQualityDetailsProps {
  quality: ScheduleScoreQualityResponse;
  getScheduleQualityString: (score: number) => ScheduleScoreQualityResult;
}

export const ScheduleQualityDetails: FC<ScheduleQualityDetailsProps> = ({ quality, getScheduleQualityString }) => {
  const { total_score: score, comments, overloaded_users } = quality;
  const [expanded, setExpanded] = useState<boolean>(false);

  const handleExpandClick = useCallback(() => {
    setExpanded((expanded) => !expanded);
  }, []);

  const infoComments = comments.filter((c) => c.type === 'info');
  const warningComments = comments.filter((c) => c.type === 'warning');

  return (
    <div className={cx('root')} data-testid="schedule-quality-details">
      <div className={cx('container')}>
        <div className={cx('container', 'container--withLateralPadding')}>
          <Text type={cx('secondary', 'header')}>
            Schedule quality:{' '}
            <Text style={{ color: getScheduleQualityMatchingColor(score) }} className={cx('header__subText')}>
              {getScheduleQualityString(score)}
            </Text>
          </Text>
          <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        </div>

        <div className={cx('container', 'container--withTopPadding', 'container--withLateralPadding')}>
          {comments?.length > 0 && (
            <>
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
            </>
          )}

          {overloaded_users?.length > 0 && (
            <div className={cx('container')}>
              <div className={cx('row')}>
                <Icon name="users-alt" />
                <div className={cx('container')}>
                  <Text type="secondary">Overloaded users</Text>
                  {overloaded_users.map((overloadedUser, index) => (
                    <Text type="primary" className={cx('username')} key={index}>
                      {overloadedUser.username} (+{overloadedUser.score}% avg)
                    </Text>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={cx('thin-line-break')} />

        <div className={cx('container', 'container--withTopPadding', 'container--withLateralPadding')}>
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
              The next 52 weeks (~1 year) are taken into account when generating the quality report. Refer to the{' '}
              <a
                href={'https://grafana.com/docs/oncall/latest/on-call-schedules/web-schedule/#schedule-quality-report'}
                target="_blank"
                rel="noreferrer"
                className={cx('link')}
              >
                <Text type="link">documentation</Text>
              </a>{' '}
              for more details.
            </Text>
          )}
        </div>
      </div>
    </div>
  );

  function getScheduleQualityMatchingColor(score: number): string {
    if (score < 20) {
      return getVar('--tag-text-danger');
    }
    if (score < 60) {
      return getVar('--tag-text-warning');
    }
    return getVar('--tag-text-success');
  }
};
