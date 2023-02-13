import React, { FC, useCallback, useState } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import { ScheduleScoreQualityResponse, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';

import Text, { TextType } from 'components/Text/Text';

import styles from './ScheduleQualityDetails.module.scss';
import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';

const cx = cn.bind(styles);

interface ScheduleQualityDetailsProps {
  quality: ScheduleScoreQualityResponse;
}

export const ScheduleQualityDetails: FC<ScheduleQualityDetailsProps> = ({ quality }) => {
  const { total_score: score } = quality;
  const [expanded, setExpanded] = useState<boolean>(false);

  const handleExpandClick = useCallback(() => {
    setExpanded((expanded) => !expanded);
  }, []);

  console.log(getScheduleQualityMatchingColor(score));

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <Text type="secondary">
          Schedule quality:{' '}
          <Text type={getScheduleQualityMatchingColor(score)}>{getScheduleQualityFromNumber(score)}</Text>
        </Text>
        <div className={cx('progress')}>
          <div
            style={{ width: `${score}%` }}
            className={cx('progress-filler', {
              [`progress-filler__type_${'success'}`]: true,
            })}
          >
            <div
              className={cx('quality-text', {
                [`quality-text__type_${'success'}`]: true,
              })}
            >
              {score}%
            </div>{' '}
          </div>
        </div>
        <ScheduleQualityProgressBar completed={quality.total_score} numTotalSteps={5} />
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Icon name="info-circle" />
              <Text type="secondary">Calculation methodology</Text>
            </HorizontalGroup>
            <IconButton name="angle-down" onClick={handleExpandClick} />
          </HorizontalGroup>
          {expanded && (
            <Text type="secondary">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer elementum purus egestas porta ultricies.
              Sed quis maximus sem. Phasellus semper pulvinar sapien ac euismod.
            </Text>
          )}
        </VerticalGroup>
      </VerticalGroup>
    </div>
  );
};

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
