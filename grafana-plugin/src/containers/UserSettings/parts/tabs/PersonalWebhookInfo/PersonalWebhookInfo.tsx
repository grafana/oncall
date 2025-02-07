import React, { useEffect, useMemo, useState } from 'react';

import { css } from '@emotion/css';
import { LoadingPlaceholder, Button, Select, Stack, Field, TextArea } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';
import { Controller, useForm } from 'react-hook-form';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { ActionKey } from 'models/loader/action-keys';
import { WebhookTriggerType } from 'models/outgoing_webhook/outgoing_webhook.types'
import { useStore } from 'state/useStore';

interface FormFields {
  webhook: string;
  context: string;
}

function useLoadingWebhooks() {
  const { loaderStore } = useStore();
  const [isLoading, setIsLoading] = React.useState(true)
  const isLoadingWebhooks = loaderStore.isLoading(ActionKey.FETCH_WEBHOOKS)
  const [hasRegisteredLoadingWebhooks, setHasRegisteredLoadingWebhooks] = useState(false);

  useEffect(() => {
    if (isLoadingWebhooks === true) {
      setHasRegisteredLoadingWebhooks(true);
    }
  }, [isLoadingWebhooks]);

  useEffect(() => {
    if (!isLoadingWebhooks && hasRegisteredLoadingWebhooks) {
      setIsLoading(false);
    }
  }, [isLoadingWebhooks])

  return isLoading;
}

const defaultValues = { webhook: null, context: '{}' }

export const PersonalWebhookInfo = observer(() => {
  const { userStore, outgoingWebhookStore } = useStore();

  const {
    formState: {
      isDirty,
      isValid,
      errors,
    },
    watch,
    control,
    getValues,
    handleSubmit,
    reset,
  } = useForm<FormFields>({
    mode: 'onBlur',
    defaultValues
  });

  const user = userStore.items[userStore.currentUserPk];
  const selectedWebhook = watch('webhook');
  const hasConnectedWebhook = user.messaging_backends.WEBHOOK != null;
  const isLoadingWebhooks = useLoadingWebhooks()

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
    reset({
      webhook: webhook ?? null,
      context: context ? JSON.stringify(context, null, 2) : '{}',
    })
  }, [userStore.personalWebhook]);

  const options = useMemo(() =>
    Object.values(outgoingWebhookStore.items).map((item) => ({
      label: item.name,
      value: item.id,
    })), [outgoingWebhookStore.items]);

  async function onFormSubmit() {
    const values = getValues();
    const webhook = values.webhook === '' ? null : values.webhook;
    const context = JSON.parse(values.context);
    userStore.addPersonalWebook({ webhook, context });
  }

  async function handleDisconnectPersonalWebhook() {
    await userStore.removePersonalWebhook();
    reset(defaultValues);
  };

  if (isLoadingWebhooks) {
    return (
      <Stack justifyContent="center" >
        <LoadingPlaceholder text="Loading..." />
      </Stack>
    )
  }

  if (!isLoadingWebhooks && !hasConnectedWebhook && options.length === 0) {
    return (
      <Stack direction="column" alignItems="center" gap={StackSize.lg}>
        <Text type="secondary">
          No webhooks found. Make sure you have added at least one webhook with the Trigger Type set to "Personal Notification".
        </Text>
        <PluginLink query={{ page: 'outgoing_webhooks' }}>
          <Button variant="primary">
            Go to Outgoing Webhooks
          </Button>
        </PluginLink>
      </Stack>
    )
  }

  return (
    <Stack direction="column" alignItems="flex-start" gap={StackSize.lg}>
      <form className={styles.form}>
        <Field label="Webhook"  >
          <Controller
            name="webhook"
            control={control}
            render={({ field }) =>
              <Select
                {...field}
                placeholder={(user.messaging_backends?.WEBHOOK?.name as string) ?? 'Select a webhook'}
                menuShouldPortal
                onChange={({ value }) => field.onChange(value)}
                isLoading={isLoadingWebhooks}
                options={options}
              />
            }
          />
        </Field>
        {selectedWebhook != null ? (
          <Field
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
        <Stack direction="row" gap={2} justifyContent="flex-end">
          {hasConnectedWebhook ? (
            <WithConfirm title={`Are you sure you want to disconnect the webhook named "${user.messaging_backends.WEBHOOK?.name}"?`} confirmText="Disconnect">
              <Button
                variant="destructive"
                onClick={handleDisconnectPersonalWebhook}
              >Disconnect</Button>
            </WithConfirm>
          ) : null}
          <Button type="submit" variant="primary" disabled={!isDirty || !isValid} onClick={handleSubmit(onFormSubmit)}>
            {hasConnectedWebhook ? 'Update' : 'Connect'}
          </Button>
        </Stack>
      </form>
    </Stack>
  );
});

const styles = {
  form: css`
    width: 100%;
  `,
}
