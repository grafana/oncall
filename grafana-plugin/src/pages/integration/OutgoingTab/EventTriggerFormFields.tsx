import React, { FC } from 'react';

import { Field, Icon, Label, Select, Tooltip, useStyles2 } from '@grafana/ui';
import { Control, Controller } from 'react-hook-form';

import { WEBHOOK_TRIGGGER_TYPE_OPTIONS } from 'models/outgoing_webhook/outgoing_webhook.types';

import { getStyles } from './OutgoingTab.styles';

interface EventTriggerFormFieldsProps {
  control: Control;
}

export const EventTriggerFormFields: FC<EventTriggerFormFieldsProps> = ({ control }) => {
  const styles = useStyles2(getStyles);

  return (
    <>
      <Field
        key="targetCloseStatusID"
        label={
          <Label>
            <span>Event trigger type</span>&nbsp;
            <Tooltip content="Some description" placement="right">
              <Icon name="info-circle" />
            </Tooltip>
          </Label>
        }
        className={styles.select}
      >
        <Controller
          control={control}
          name="fields.targetCloseStatusID"
          rules={{
            required: 'Trigger type is required',
          }}
          render={({ field }) => (
            <Select
              menuShouldPortal
              options={WEBHOOK_TRIGGGER_TYPE_OPTIONS}
              placeholder="Select event"
              value={field.value}
              onChange={({ value }) => {
                field.onChange(value);
              }}
            />
          )}
        />
      </Field>
    </>
  );
};
