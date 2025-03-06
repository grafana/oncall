import React, { useEffect, useMemo, useState } from 'react';

import { css } from '@emotion/css';
import { LoadingPlaceholder, Button, Select, Stack, Field, TextArea, Icon } from '@grafana/ui';
import { PLUGIN_ROOT, StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';
import { Controller, useForm } from 'react-hook-form';

import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { ActionKey } from 'models/loader/action-keys';
import { WebhookTriggerType } from 'models/outgoing_webhook/outgoing_webhook.types'
import { useStore } from 'state/useStore';

function useWebhooksOptions(): [boolean, Array<{ label: string, value: string }>] {
  const { outgoingWebhookStore, loaderStore } = useStore();
  const [isLoading, setIsLoading] = useState(true)
  const isLoadingWebhooks = loaderStore.isLoading(ActionKey.FETCH_WEBHOOKS)
  const [hasRegisteredLoadingWebhooks, setHasRegisteredLoadingWebhooks] = useState(false);

  const webhookOptions = useMemo(() =>
    Object.values(outgoingWebhookStore.items).map((item) => ({
      label: item.name,
      value: item.id,
    })), [outgoingWebhookStore.items]);


  useEffect(() => {
    if (isLoadingWebhooks) {
      setHasRegisteredLoadingWebhooks(true);
    }
  }, [isLoadingWebhooks]);

  useEffect(() => {
    if (!isLoadingWebhooks && hasRegisteredLoadingWebhooks) {
      setIsLoading(false);
    }
  }, [isLoadingWebhooks])

  return [isLoading, webhookOptions];
}

const contextRules = {
  validate(value: string) {
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
}

interface FormFields {
  webhook: string;
  context: string;
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
    mode: 'onChange',
    defaultValues
  });

  const user = userStore.items[userStore.currentUserPk];
  const selectedWebhook = watch('webhook');
  const [isLoadingOptions, webhookOptions] = useWebhooksOptions()

  const hasConnectedWebhook = user.messaging_backends?.WEBHOOK != null;
  const hasSelectedValidWebhook = webhookOptions.some(option => option.value === selectedWebhook)

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

  if (isLoadingOptions) {
    return (
      <Stack justifyContent="center" >
        <LoadingPlaceholder text="Loading..." />
      </Stack>
    )
  }

  return (
    <Stack direction="column" alignItems="flex-start" gap={StackSize.lg}>
      <form className={styles.form}>
        <Field
          label="Add webhook to send personal notifications"
          description={
            <p>The list only displays webhooks that have Personal notification as a trigger.
              <a href={`${PLUGIN_ROOT}/outgoing_webhooks`} target="_blank" rel="noreferrer" className={styles.link}>
                <Text type="link">
                  <span>Configure</span>
                  <Icon
                    name="external-link-alt"
                    className={styles.linkIcon}
                  />
                </Text>
              </a>
            </p>
          }
        >
          <Controller
            name="webhook"
            control={control}
            render={({ field }) =>
              <Select
                {...field}
                menuShouldPortal
                placeholder={(user.messaging_backends?.WEBHOOK?.name as string) ?? 'Select webhook'}
                onChange={({ value }) => field.onChange(value)}
                options={webhookOptions}
              />
            }
          />
        </Field>
        {
          selectedWebhook != null ? (
            <Field
              label="Context"
              description={
                <p>You can add additional JSON context to be used by the webhook templates allowing for webhook reusability between different users.
                  <a href={"https://grafana.com/docs/oncall/latest/manage/notify/webhook/"} target="_blank" rel="noreferrer" className={styles.link}>
                    <Text type="link">
                      <span>Learn more in docs</span>
                      <Icon
                        name="external-link-alt"
                        className={styles.linkIcon}
                      />
                    </Text>
                  </a>
                </p>
              }
              invalid={!!errors.context}
              error={errors.context?.message}
            >
              <Controller
                name="context"
                control={control}
                rules={contextRules}
                render={({ field }) => <TextArea {...field} rows={8} />}
              />
            </Field>
          ) : null
        }
        <Stack direction="row" gap={2}>
          <Button
            type="submit"
            variant="primary" disabled={!isDirty || !isValid || !hasSelectedValidWebhook}
            onClick={handleSubmit(onFormSubmit)}
          >
            {hasConnectedWebhook ? 'Save' : 'Connect'}
          </Button>
          {hasConnectedWebhook ? (
            <WithConfirm
              title={`Are you sure you want to disconnect the webhook named "${user.messaging_backends.WEBHOOK?.name}"?`}
              confirmText="Disconnect"
            >
              <Button
                variant="destructive"
                onClick={handleDisconnectPersonalWebhook}
              >Disconnect</Button>
            </WithConfirm>
          ) : null}
        </Stack>
      </form >
    </Stack >
  );
});

const styles = {
  form: css`
    width: 100%;

    & > div {
      margin-bottom: 24px;
    }

    & > div:last-child {
      margin-bottom: 0;
    }

    div {
      max-width: unset;
    }
    
    p {
      margin-bottom: 8px;
    }
  `,
  link: css`
    margin-left: 8px;
  `,
  linkIcon: css`
    margin-left: 4px;
    margin-bottom: 2px;
  `
}
