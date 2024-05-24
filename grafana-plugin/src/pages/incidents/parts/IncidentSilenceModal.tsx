import React, { useState } from 'react';

import { css } from '@emotion/css';
import {
  DateTime,
  addDurationToDate,
  dateTime,
  durationToMilliseconds,
  intervalToAbbreviatedDurationString,
  isValidDuration,
  parseDuration,
} from '@grafana/data';
import { Button, DateTimePicker, Field, HorizontalGroup, Input, Modal, useStyles2 } from '@grafana/ui';

import { useDebouncedCallback } from 'utils/hooks';

interface IncidentSilenceModalProps {
  isOpen: boolean;
  alertGroupID: string;
  alertGroupName: string;

  onDismiss: () => void;
  onSave: (value: number) => void;
}

const IncidentSilenceModal: React.FC<IncidentSilenceModalProps> = ({
  isOpen,
  alertGroupID,
  alertGroupName,

  onDismiss,
  onSave,
}) => {
  const [date, setDate] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));
  const [duration, setDuration] = useState<string>('');
  const debouncedUpdateDateTime = useDebouncedCallback(updateDateTime, 500);

  const styles = useStyles2(getStyles);
  const isDurationValid = isValidDuration(duration);

  return (
    <Modal
      onDismiss={onDismiss}
      closeOnBackdropClick={false}
      isOpen={isOpen}
      title={`Silence alert group #${alertGroupID} ${alertGroupName}`}
      className={styles.root}
    >
      <div className={styles.container}>
        <Field key={'SilencePicker'} label={'Silence End'} className={styles.containerChild}>
          <DateTimePicker label="Date" date={date} onChange={onDateChange} minDate={new Date()} />
        </Field>

        <Field key={'Duration'} label={'Duration'} className={styles.containerChild} invalid={!isDurationValid}>
          <Input value={duration} onChange={onDurationChange} placeholder="Enter duration (2h 30m)" />
        </Field>
      </div>

      <HorizontalGroup justify="flex-end">
        <Button variant={'secondary'} onClick={onDismiss}>
          Cancel
        </Button>
        <Button variant={'primary'} onClick={onSubmit} disabled={!isDurationValid}>
          Add
        </Button>
      </HorizontalGroup>
    </Modal>
  );

  function onDateChange(date: DateTime) {
    setDate(date);
    const duration = intervalToAbbreviatedDurationString({
      start: new Date(),
      end: new Date(date.toDate()),
    });
    setDuration(duration);
  }

  function onDurationChange(event: React.SyntheticEvent<HTMLInputElement>) {
    const newDuration = event.currentTarget.value;
    if (newDuration !== duration) {
      setDuration(newDuration);
      debouncedUpdateDateTime(newDuration);
    }
  }

  function updateDateTime(newDuration: string) {
    setDate(dateTime(addDurationToDate(new Date(), parseDuration(newDuration))));
  }

  function onSubmit() {
    onSave(durationToMilliseconds(parseDuration(duration)) / 1000);
  }
};

const getStyles = () => ({
  root: css`
    width: 600px;
  `,

  container: css`
    width: 100%;
    display: flex;
    column-gap: 16px;
  `,
  containerChild: css`
    flex-grow: 1;
  `,
});

export { IncidentSilenceModal };
