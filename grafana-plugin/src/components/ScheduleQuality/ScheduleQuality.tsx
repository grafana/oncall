import React, { FC, useEffect, useState } from 'react';

import cn from 'classnames/bind';
import styles from './ScheduleQuality.module.css';
import { useStore } from 'state/useStore';
import { Schedule, ScheduleScoreQualityResponse } from 'models/schedule/schedule.types';
import { ScheduleQualityDetails } from 'components/ScheduleQualityDetails/ScheduleQualityDetails';
import Text from 'components/Text/Text';
import { HorizontalGroup, Tooltip } from '@grafana/ui';

const cx = cn.bind(styles);

interface ScheduleQualityProps {
  scheduleId: Schedule['id'];
}

const ScheduleQuality: FC<ScheduleQualityProps> = ({ scheduleId }) => {
  const { scheduleStore } = useStore();
  const [qualityResponse, setQualityResponse] = useState<ScheduleScoreQualityResponse>(undefined);

  useEffect(() => {
    if (scheduleId) {
      fetchScoreQuality();
    }
  }, [scheduleId]);

  if (!qualityResponse) return null;

  return (
    <>
      <ScheduleQualityDetails quality={qualityResponse} />
      <Tooltip placement="bottom-end" interactive content={<ScheduleQualityDetails quality={qualityResponse} />}>
        <div className={cx('root')}>
          <HorizontalGroup spacing="sm">
            <Text type="secondary">Quality:</Text>
            <Text type="primary">{qualityResponse.total_score}%</Text>
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
