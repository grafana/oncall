import React, { useState } from 'react';

import { css, cx } from '@emotion/css';
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
import { Controller, useForm } from 'react-hook-form';
import { bem, getUtilStyles } from 'styles/utils.styles';

import { Text } from 'components/Text/Text';
import { useDebouncedCallback } from 'utils/hooks';
import { openWarningNotification } from 'utils/utils';

interface IncidentSilenceModalProps {
  isOpen: boolean;
  alertGroupID: number;
  alertGroupName: string;

  onDismiss: () => void;
  onSave: (value: number) => void;
}

interface FormFields {
  duration: string;
}

const IncidentSilenceModal: React.FC<IncidentSilenceModalProps> = ({
  isOpen,
  alertGroupID,
  alertGroupName,

  onDismiss,
  onSave,
}) => {
  const [date, setDate] = useState<DateTime>(dateTime());
  const debouncedUpdateDateTime = useDebouncedCallback(updateDateTime, 500);

  const styles = useStyles2(getStyles);
  const utilStyles = useStyles2(getUtilStyles);

  const {
    control,
    setValue,
    getValues,
    handleSubmit,
    formState: { errors },
  } = useForm<FormFields>({
    mode: 'onSubmit',
  });

  return (
    <Modal
      onDismiss={onDismiss}
      closeOnBackdropClick={false}
      isOpen={isOpen}
      title={
        <Text.Title
          level={4}
          type="primary"
          className={cx(utilStyles.overflowChild, bem(utilStyles.overflowChild, 'line-1'))}
        >
          Silence alert group #{alertGroupID} ${alertGroupName}
        </Text.Title>
      }
      className={styles.root}
    >
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <div className={styles.container}>
          <Field key={'SilencePicker'} label={'Silence'} className={styles.containerChild}>
            <div className={styles.datePicker}>
              <DateTimePicker
                showSeconds={false}
                label="Date"
                date={date}
                onChange={onDateChange}
                minDate={new Date()}
              />
            </div>
          </Field>

          <Controller
            name={'duration'}
            control={control}
            rules={{
              required: 'Duration is required',
              validate: (value: string) => {
                return value?.trim() && isValidDuration(value) ? true : 'Duration is invalid';
              },
            }}
            render={({ field }) => (
              <Field
                key={'Duration'}
                label={'Duration'}
                invalid={!!errors.duration}
                error={errors.duration?.message}
                className={styles.containerChild}
              >
                <Input
                  {...field}
                  value={field.value}
                  onChange={(event: React.FormEvent<HTMLInputElement>) => {
                    const newDuration: string = event.currentTarget.value;
                    field.onChange(newDuration);

                    debouncedUpdateDateTime(newDuration);
                  }}
                  placeholder="Enter duration (2h 30m)"
                />
              </Field>
            )}
          />
        </div>

        <HorizontalGroup justify="flex-end">
          <Button variant={'secondary'} onClick={onDismiss}>
            Cancel
          </Button>
          <Button type="submit" variant={'primary'} disabled={!!errors.duration?.message}>
            Silence
          </Button>
        </HorizontalGroup>
      </form>
    </Modal>
  );

  function onFormSubmit() {
    onSave(durationToMilliseconds(parseDuration(getValues('duration'))) / 1000);
  }

  function onDateChange(newDate: DateTime) {
    const duration = intervalToAbbreviatedDurationString({
      start: new Date(),
      end: new Date(newDate.toDate()),
    });

    if (!duration) {
      openWarningNotification('Silence Date is either invalid or in the past');
    } else {
      setDate(newDate);
      setValue('duration', duration);
    }
  }

  function updateDateTime(newDuration: string) {
    setDate(dateTime(addDurationToDate(new Date(), parseDuration(newDuration))));
  }
};

const getStyles = () => ({
  root: css`
    width: 600px;
  `,

  container: css`
    width: 100%;
    display: flex;
    column-gap: 8px;
  `,
  containerChild: css`
    flex-basis: 50%;
  `,
  datePicker: css`
    label {
      display: none;
    }
  `,
});

export { IncidentSilenceModal };
