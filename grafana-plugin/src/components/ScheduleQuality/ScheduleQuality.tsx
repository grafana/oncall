import React, { FC, useEffect, useState } from 'react';

import { HorizontalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import { ScheduleQualityDetails } from 'components/ScheduleQualityDetails/ScheduleQualityDetails';
import Text from 'components/Text/Text';
import { Schedule, ScheduleScoreQualityResponse } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import styles from './ScheduleQuality.module.css';

const cx = cn.bind(styles);

interface ScheduleQualityProps {
  scheduleId: Schedule['id'];
  lastUpdated: number;
}

const ScheduleQuality: FC<ScheduleQualityProps> = ({ scheduleId, lastUpdated }) => {
  const { scheduleStore } = useStore();
  const [qualityResponse, setQualityResponse] = useState<ScheduleScoreQualityResponse>(undefined);

  useEffect(() => {
    if (scheduleId) {
      fetchScoreQuality();
    }
  }, [scheduleId, lastUpdated]);

  if (!qualityResponse) {
    return null;
  }

  return (
    <>
      <Tooltip placement="bottom-start" interactive content={<ScheduleQualityDetails quality={qualityResponse} />}>
        <div className={cx('root')}>
          <HorizontalGroup spacing="sm">
            <Text type="secondary" className="u-cursor-default">
              Quality:
            </Text>
            <Text type="primary" className="u-cursor-default">
              {qualityResponse.total_score}%
            </Text>
          </HorizontalGroup>
        </div>
      </Tooltip>
    </>
  );

  async function fetchScoreQuality() {
    const qualityResponse = await scheduleStore.getScoreQuality(scheduleId);
    setQualityResponse(qualityResponse);
  }
};

export default ScheduleQuality;
