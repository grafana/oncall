import React, { useEffect } from 'react';

import { css } from '@emotion/css';
import { Button, Select, Stack, Field, TextArea } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';
import { Controller, useForm } from 'react-hook-form';

import { ActionKey } from 'models/loader/action-keys';
import { WebhookTriggerType } from 'models/outgoing_webhook/outgoing_webhook.types'
import { useStore } from 'state/useStore';

interface FormFields {
  webhook: string;
  context: string;
}

export const PersonalWebhookInfo = observer(() => {
  const { userStore, outgoingWebhookStore, loaderStore } = useStore();

  const {
    formState: {
      isDirty,
      isValid,
      errors,
    },
    watch,
    control,
    getValues,
    setValue,
    handleSubmit,
  } = useForm<FormFields>({
    mode: 'onBlur',
    defaultValues: { webhook: '', context: '{}' }
  });

  function onFormSubmit() {
    const values = getValues();
    const webhook = values.webhook === '' ? null : values.webhook;
    const context = JSON.parse(values.context);
    userStore.addPersonalWebook({ webhook, context });
  }

  useEffect(() => {
    (async () => {
      await userStore.updatePersonalWebhook();
      await outgoingWebhookStore.updateItems(
        {
          trigger_type: WebhookTriggerType.PersonalNotification.key,
        },
        true
      );
    })();
  }, []);

  useEffect(() => {
    const { webhook, context } = userStore.personalWebhook ?? {};
    setValue('webhook', webhook ?? '');
    setValue('context', context ? JSON.stringify(context, null, 2) : '{}');
  }, [userStore.personalWebhook]);

  const options = [
    { label: 'None', value: '' },
    ...Object.values(outgoingWebhookStore.items).map((item) => ({
      label: item.name,
      value: item.id,
    }))];

  const webhook = watch('webhook');
  return (
    <Stack direction="column" alignItems="flex-start" gap={StackSize.lg}>
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <Field label="Webhook" className={styles.field} >
          <Controller
            name="webhook"
            control={control}
            render={({ field }) =>
              <Select
                {...field}
                menuShouldPortal
                onChange={({ value }) => field.onChange(value)}
                isLoading={loaderStore.isLoading(ActionKey.FETCH_WEBHOOKS)}
                options={options}
              />
            }
          />
        </Field>
        {webhook !== '' ? (
          <Field
            className={styles.field}
            label="Context"
            invalid={!!errors.context}
            error={errors.context?.message}
          >
            <Controller
              name="context"
              control={control}
              rules={{
                validate(value) {
                  let context: object;
                  try {
                    context = JSON.parse(value);
                  } catch (_) {
                    return 'Invalid JSON';
                  }
                  if (typeof context !== 'object' || context === null || Array.isArray(context)) {
                    return 'JSON must be an object';
                  }
                  return true;
                }
              }}
              render={({ field }) =>
                <TextArea
                  {...field}
                  rows={8}
                />
              }
            />
          </Field>
        ) : null}
        <Button type="submit" variant={'primary'} disabled={!isDirty || !isValid}>
          Save
        </Button>
      </form>
    </Stack>
  );
});

const styles = {
  field: css`
    width: 100%;
  `,
}
