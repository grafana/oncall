import React from 'react';

import { PENDING_COLOR, Tooltip, Icon } from '@grafana/ui';

import { Schedule } from 'models/schedule/schedule.types';

interface ScheduleWarningProps {
  item: Schedule;
}

const ScheduleWarning = (props: ScheduleWarningProps) => {
  const { item } = props;
  if (item.warnings.length > 0) {
    const tooltipContent = (
      <div>
        {item.warnings.map((warning: string, key: number) => (
          <p key={key}>{warning}</p>
        ))}
      </div>
    );
    return (
      <Tooltip placement="top" content={tooltipContent}>
        <Icon style={{ color: PENDING_COLOR }} name="exclamation-triangle" />
      </Tooltip>
    );
  }

  return null;
};

export default ScheduleWarning;
