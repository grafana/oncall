import React, { FC, useCallback, useState } from 'react';

import { dateTime, DateTime } from '@grafana/data';
import {
  IconButton,
  VerticalGroup,
  HorizontalGroup,
  Field,
  Input,
  Button,
  DateTimePicker,
  Select,
  InlineSwitch,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  layerId: string;
  onHide: () => void;
  id: number | 'new';
}

const cx = cn.bind(styles);

const RotationForm: FC<RotationFormProps> = (props) => {
  const { onHide } = props;

  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<string>('days');
  const [selectedDays, setSelectedDays] = useState<string[]>(['Tuesday']);
  const [shiftStart, setShiftStart] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));
  const [shiftEnd, setShiftEnd] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));
  const [rotationStart, setRotationStart] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));

  const handleChangeEndless = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndless(!event.currentTarget.checked);
    },
    [endLess]
  );

  const handleRepeatEveryValueChange = useCallback((option) => {
    setRepeatEveryValue(option.value);
  }, []);

  const handleRepeatEveryPeriodChange = useCallback((option) => {
    setRepeatEveryPeriod(option.value);
  }, []);

  const moment = dayjs();

  return (
    <Modal
      width="430px"
      title="New Rotation"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" positionOffset={{ x: 0, y: 0 }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text size="medium">Rotation 1</Text>
          <HorizontalGroup>
            <IconButton variant="secondary" tooltip="Copy" name="copy" />
            <IconButton variant="secondary" tooltip="Code" name="brackets-curly" />
            <IconButton variant="secondary" tooltip="Delete" name="trash-alt" />
            <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
          </HorizontalGroup>
        </HorizontalGroup>
        <UserGroups />
        {/*<hr />*/}
        <VerticalGroup>
          <HorizontalGroup>
            <Field className={cx('control')} label="Repeat shifts every">
              <Select
                value={repeatEveryValue}
                options={[
                  { label: '1', value: 1 },
                  { label: '2', value: 2 },
                  { label: '3', value: 3 },
                  { label: '4', value: 4 },
                  { label: '5', value: 5 },
                  { label: '6', value: 6 },
                ]}
                onChange={handleRepeatEveryValueChange}
              />
            </Field>
            <Field className={cx('control')} label="">
              <Select
                value={repeatEveryPeriod}
                options={[
                  { label: 'days', value: 'days' },
                  { label: 'weeks', value: 'weeks' },
                  { label: 'hours', value: 'hours' },
                ]}
                onChange={handleRepeatEveryPeriodChange}
              />
            </Field>
          </HorizontalGroup>
          {repeatEveryPeriod === 'weeks' && (
            /*<HorizontalGroup justify="center">*/
            <Field label="Select days to repeat">
              <DaysSelector value={selectedDays} onChange={(value) => setSelectedDays(value)} />
            </Field>
            /*</HorizontalGroup>*/
          )}
          <HorizontalGroup>
            <Field className={cx('date-time-picker')} label="Shift start">
              <DateTimePicker date={shiftStart} onChange={setShiftStart} />
            </Field>
            <Field className={cx('date-time-picker')} label="Shift end">
              <DateTimePicker date={shiftEnd} onChange={setShiftEnd} />
            </Field>
          </HorizontalGroup>
          <HorizontalGroup>
            <Field className={cx('date-time-picker')} label="Rotation start">
              <DateTimePicker date={rotationStart} onChange={setRotationStart} />
            </Field>
            <Field
              label={
                <HorizontalGroup spacing="xs">
                  <Text type="primary" size="small">
                    Rotation end
                  </Text>
                  <InlineSwitch
                    className={cx('inline-switch')}
                    transparent
                    value={!endLess}
                    onChange={handleChangeEndless}
                  />
                </HorizontalGroup>
              }
            >
              {endLess ? (
                <Input
                  value="endless"
                  onClick={() => {
                    setEndless(false);
                  }}
                />
              ) : (
                <DateTimePicker date={rotationEnd} onChange={setRotationEnd} />
              )}
            </Field>
          </HorizontalGroup>
        </VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Timezone: {getTzOffsetString(moment)}</Text>
          <HorizontalGroup>
            <Button variant="secondary">+ Override</Button>
            <Button variant="primary">Create</Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface DaysSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
}

const DaysSelector = ({ value, onChange }: DaysSelectorProps) => {
  const getDayClickHandler = (day: string) => {
    return () => {
      const newValue = [...value];
      if (newValue.includes(day)) {
        const index = newValue.indexOf(day);
        newValue.splice(index, 1);
      } else {
        newValue.push(day);
      }
      onChange(newValue);
    };
  };

  return (
    <div className={cx('days')}>
      {DAYS.map((day: string) => (
        <div onClick={getDayClickHandler(day)} className={cx('day', { day__selected: value.includes(day) })}>
          {day.charAt(0).toUpperCase()}
        </div>
      ))}
    </div>
  );
};

export default RotationForm;
