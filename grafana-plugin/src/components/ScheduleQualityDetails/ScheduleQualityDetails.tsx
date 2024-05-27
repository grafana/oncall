import React, { FC, useCallback, useState } from 'react';

import { cx } from '@emotion/css';
import { HorizontalGroup, Icon, IconButton, useStyles2 } from '@grafana/ui';
import { bem, getUtilStyles } from 'styles/utils.styles';

import { Text } from 'components/Text/Text';
import { ScheduleScoreQualityResponse, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';

import { getScheduleQualityDetailsStyles } from './ScheduleQualityDetails.styles';
import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';

interface ScheduleQualityDetailsProps {
  quality: ScheduleScoreQualityResponse;
  getScheduleQualityString: (score: number) => ScheduleScoreQualityResult;
}

export const ScheduleQualityDetails: FC<ScheduleQualityDetailsProps> = ({ quality, getScheduleQualityString }) => {
  const { total_score: score, comments, overloaded_users } = quality;
  const [expanded, setExpanded] = useState<boolean>(false);

  const utils = useStyles2(getUtilStyles);
  const styles = useStyles2(getScheduleQualityDetailsStyles);

  const handleExpandClick = useCallback(() => {
    setExpanded((expanded) => !expanded);
  }, []);

  const infoComments = comments.filter((c) => c.type === 'info');
  const warningComments = comments.filter((c) => c.type === 'warning');

  return (
    <div className={styles.root} data-testid="schedule-quality-details">
      <div className={styles.container}>
        <div className={cx(styles.container, bem(styles.container, 'withLateralPadding'))}>
          <Text type="secondary" className={styles.header}>
            Schedule quality:{' '}
            <Text type="primary" className={styles.headerSubText}>
              {getScheduleQualityString(score)}
            </Text>
          </Text>
          <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        </div>

        <div
          className={cx(
            styles.container,
            bem(styles.container, 'withTopPadding'),
            bem(styles.container, 'withLateralPadding')
          )}
        >
          {comments?.length > 0 && (
            <>
              {/* Show Info comments */}
              {infoComments?.length > 0 && (
                <div className={styles.container}>
                  <div className={styles.row}>
                    <Icon name="info-circle" />
                    <div className={styles.container}>
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
                <div className={styles.container}>
                  <div className={styles.row}>
                    <Icon name="calendar-alt" />
                    <div className={styles.container}>
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
            <div className={styles.container}>
              <div className={styles.row}>
                <Icon name="users-alt" />
                <div className={styles.container}>
                  <Text type="secondary">Overloaded users</Text>
                  {overloaded_users.map((overloadedUser, index) => (
                    <Text type="primary" className={styles.username} key={index}>
                      {overloadedUser.username} (+{overloadedUser.score}% avg)
                    </Text>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={cx(utils.thinLineBreak)} />

        <div
          className={cx(
            styles.container,
            bem(styles.container, 'withTopPadding'),
            bem(styles.container, 'withLateralPadding')
          )}
        >
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Icon name="calculator-alt" />
              <Text type="secondary" className={styles.metholodogy}>
                Calculation methodology
              </Text>
            </HorizontalGroup>
            <IconButton
              aria-label={expanded ? 'Collapse' : 'Expand'}
              name={expanded ? 'arrow-down' : 'arrow-right'}
              onClick={handleExpandClick}
            />
          </HorizontalGroup>
          {expanded && (
            <Text type="primary" className={styles.text}>
              The next 52 weeks (~1 year) are taken into account when generating the quality report. Refer to the{' '}
              <a
                href={'https://grafana.com/docs/oncall/latest/on-call-schedules/web-schedule/#schedule-quality-report'}
                target="_blank"
                rel="noreferrer"
                className={cx(utils.link)}
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
};
