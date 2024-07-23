import React, { useState } from 'react';

import { dateMath, DateTime, TimeRange, toUtc } from '@grafana/data';
import { TimeZone } from '@grafana/schema';
import { TimeRangePicker } from '@grafana/ui';
import { noop } from 'lodash';

interface TimeRangePickerProps {
  value: TimeRange;
  timeZone: string;

  onChange: (timeRange: TimeRange) => void;
}

export function TimeRangePickerWrapper(props: TimeRangePickerProps) {
  const { onChange } = props;

  const [value, setValue] = useState<TimeRange>(props.value);
  const [timezone, setTimezone] = useState<string>(props.timeZone);

  return (
    <TimeRangePicker
      isOnCanvas
      timeZone={timezone}
      value={value}
      onChange={onPickerChange}
      onZoom={onZoom}
      onMoveBackward={onMoveBackward}
      onMoveForward={onMoveForward}
      onChangeTimeZone={onTimezoneChange}
      onChangeFiscalYearStartMonth={noop}
    />
  );

  function onPickerChange(timeRange: TimeRange) {
    setValue(timeRange);
    onChange(timeRange);
  }

  function onZoom() {
    const zoomedTimeRange = getZoomedTimeRange(value, 2);
    onPickerChange(zoomedTimeRange);
  }

  function onMoveBackward() {
    onPickerChange(getShiftedTimeRange(TimeRangeDirection.Backward, value, Date.now()));
  }

  function onMoveForward() {
    onPickerChange(getShiftedTimeRange(TimeRangeDirection.Forward, value, Date.now()));
  }

  function onTimezoneChange(timeZone: TimeZone) {
    setTimezone(timeZone);
    onPickerChange(evaluateTimeRange(value.from, value.to, timeZone));
  }
}

function evaluateTimeRange(
  from: string | DateTime,
  to: string | DateTime,
  timeZone: TimeZone,
  fiscalYearStartMonth?: number,
  delay?: string
): TimeRange {
  const hasDelay = delay && to === 'now';

  return {
    from: dateMath.parse(from, false, timeZone, fiscalYearStartMonth)!,
    to: dateMath.parse(hasDelay ? 'now-' + delay : to, true, timeZone, fiscalYearStartMonth)!,
    raw: {
      from: from,
      to: to,
    },
  };
}

function getZoomedTimeRange(timeRange: TimeRange, factor: number): TimeRange {
  const timespan = timeRange.to.valueOf() - timeRange.from.valueOf();
  const center = timeRange.to.valueOf() - timespan / 2;
  // If the timepsan is 0, zooming out would do nothing, so we force a zoom out to 30s
  const newTimespan = timespan === 0 ? 30000 : timespan * factor;

  const to = center + newTimespan / 2;
  const from = center - newTimespan / 2;

  return { from: toUtc(from), to: toUtc(to), raw: { from: toUtc(from), to: toUtc(to) } };
}

enum TimeRangeDirection {
  Backward,
  Forward,
}

function getShiftedTimeRange(dir: TimeRangeDirection, timeRange: TimeRange, upperLimit: number): TimeRange {
  const oldTo = timeRange.to.valueOf();
  const oldFrom = timeRange.from.valueOf();
  const halfSpan = (oldTo - oldFrom) / 2;

  let fromRaw: number;
  let toRaw: number;
  if (dir === TimeRangeDirection.Backward) {
    fromRaw = oldFrom - halfSpan;
    toRaw = oldTo - halfSpan;
  } else {
    fromRaw = oldFrom + halfSpan;
    toRaw = oldTo + halfSpan;

    if (toRaw > upperLimit && oldTo < upperLimit) {
      toRaw = upperLimit;
      fromRaw = oldFrom;
    }
  }

  const from = toUtc(fromRaw);
  const to = toUtc(toRaw);
  return {
    from,
    to,
    raw: { from, to },
  };
}
