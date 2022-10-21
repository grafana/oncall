import React, { FC, useCallback, useState } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, IconButton, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';

import styles from './ScheduleQuality.module.css';

interface ScheduleQualityProps {
  quality: number;
}

const cx = cn.bind(styles);

const ScheduleQuality: FC<ScheduleQualityProps> = ({ quality }) => (
  <Tooltip placement="bottom-end" interactive content={<SheduleQualityDetails quality={quality} />}>
    <div className={cx('root')}>
      <HorizontalGroup spacing="sm">
        <Text type="secondary">Quality:</Text>
        <Text type="primary">{Math.floor(quality * 100)}%</Text>
      </HorizontalGroup>
    </div>
  </Tooltip>
);

interface ScheduleQualityDetailsProps {
  quality: number;
}

const SheduleQualityDetails = ({ quality }: ScheduleQualityDetailsProps) => {
  const [expanded, setExpanded] = useState<boolean>(false);

  const type = quality > 0.8 ? 'success' : 'warning';
  const qualityPercent = quality * 100;

  const handleExpandClick = useCallback(() => {
    setExpanded((expanded) => !expanded);
  }, []);

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <Text type="secondary">Schedule quality</Text>
        <div className={cx('progress')}>
          <div
            style={{ width: `${qualityPercent}%` }}
            className={cx('progress-filler', {
              [`progress-filler__type_${type}`]: true,
            })}
          >
            <div
              className={cx('quality-text', {
                [`quality-text__type_${type}`]: true,
              })}
            >
              {qualityPercent}%
            </div>{' '}
          </div>
        </div>
        {type === 'success' && (
          <Text type="primary">
            You are doing a great job! <br />
            Schedule is well balanced for all members.
          </Text>
        )}
        {type === 'warning' && <Text type="primary">Your schedule has balance problems.</Text>}
        <hr style={{ width: '100%' }} />
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

export default ScheduleQuality;
