import React, { FC, useState } from 'react';

import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  Input,
  Label,
  Select,
  Switch,
  Tooltip,
  useStyles2,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames';
import { Controller, useFormContext } from 'react-hook-form';

import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { WebhooksTemplateEditor } from 'containers/WebhooksTemplateEditor/WebhooksTemplateEditor';
import { HTTP_METHOD_OPTIONS, WEBHOOK_TRIGGGER_TYPE_OPTIONS } from 'models/outgoing_webhook/outgoing_webhook.types';

import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabFormValues } from './OutgoingTab.types';

interface TemplateToEdit {
  value: string;
  displayName: string;
  name: string;
}

interface OutgoingWebhookFormFieldsProps {
  // "new" should be used for new webhook
  webhookId: string;
}

export const OutgoingWebhookFormFields: FC<OutgoingWebhookFormFieldsProps> = ({ webhookId }) => {
  const styles = useStyles2(getStyles);
  const { control, watch, formState, register } = useFormContext<OutgoingTabFormValues>();
  const [templateToEdit, setTemplateToEdit] = useState<TemplateToEdit>();

  const [showTriggerTemplate] = watch(['triggerTemplateToogle', 'forwardedDataTemplateToogle']);

  return (
    <VerticalGroup spacing="lg">
      <div className={styles.switcherFieldWrapper}>
        <Controller
          control={control}
          name="isEnabled"
          render={({ field: { value, onChange } }) => <Switch value={value} onChange={() => onChange(!value)} />}
        />
        <Label className={styles.switcherLabel}>Enabled</Label>
      </div>
      <Controller
        control={control}
        name="triggerType"
        rules={{
          required: 'Trigger type is required',
        }}
        render={({ field }) => (
          <Field
            key="triggerType"
            invalid={Boolean(formState.errors.triggerType)}
            error={formState.errors.triggerType?.message}
            label={
              <Label>
                <span>Trigger type</span>&nbsp;
                <Tooltip content="Some description" placement="right">
                  <Icon name="info-circle" className={styles.infoIcon} />
                </Tooltip>
              </Label>
            }
            className={styles.selectField}
          >
            <Select
              {...field}
              onChange={({ value }) => field.onChange(value)}
              menuShouldPortal
              options={WEBHOOK_TRIGGGER_TYPE_OPTIONS}
              placeholder="Select event"
            />
          </Field>
        )}
      />
      <Field
        key="url"
        invalid={Boolean(formState.errors.url)}
        error={formState.errors.url?.message}
        label={
          <Label>
            <span>Webhook URL</span>&nbsp;
            <Tooltip content="Some description" placement="right">
              <Icon name="info-circle" className={styles.infoIcon} />
            </Tooltip>
          </Label>
        }
        className={styles.selectField}
      >
        <Input {...register('url', { required: 'URL is required' })} />
      </Field>
      <Controller
        control={control}
        name="httpMethod"
        rules={{
          required: 'HTTP method is required',
        }}
        render={({ field }) => (
          <Field
            key="httpMethod"
            invalid={Boolean(formState.errors.httpMethod)}
            error={formState.errors.httpMethod?.message}
            label={
              <Label>
                <span>HTTP method</span>&nbsp;
                <Tooltip content="Some description" placement="right">
                  <Icon name="info-circle" className={styles.infoIcon} />
                </Tooltip>
              </Label>
            }
            className={styles.selectField}
          >
            <Select
              {...field}
              onChange={({ value }) => field.onChange(value)}
              menuShouldPortal
              options={HTTP_METHOD_OPTIONS}
              placeholder="Select HTTP method"
            />
          </Field>
        )}
      />
      <Controller
        control={control}
        name="forwardedDataTemplate"
        render={({ field }) => (
          <VerticalGroup>
            <HorizontalGroup width="100%" justify="space-between">
              <Label className={styles.switcherLabel}>Data template</Label>
              <Button
                icon="edit"
                variant="secondary"
                onClick={() => {
                  setTemplateToEdit({
                    value: field.value,
                    displayName: 'forwarded data',
                    name: field.name,
                  });
                }}
              />
            </HorizontalGroup>
            <MonacoEditor
              {...field}
              data={{}} // TODO:update
              showLineNumbers={false}
              monacoOptions={MONACO_READONLY_CONFIG}
              onChange={field.onChange}
            />
            {templateToEdit?.['name'] === field.name && (
              <WebhooksTemplateEditor
                id={webhookId}
                handleSubmit={(value) => {
                  field.onChange(value);
                  setTemplateToEdit(undefined);
                }}
                onHide={() => setTemplateToEdit(undefined)}
                template={templateToEdit}
              />
            )}
          </VerticalGroup>
        )}
      />
      <div className={styles.triggerTemplateWrapper}>
        <div className={cn(styles.switcherFieldWrapper, styles.addTriggerTemplate)}>
          <Controller
            control={control}
            name="triggerTemplateToogle"
            render={({ field: { value, onChange } }) => <Switch value={value} onChange={() => onChange(!value)} />}
          />
          <Label className={styles.switcherLabel}>
            <span>Add trigger template</span>
            <Tooltip content="Some description" placement="right">
              <Icon name="info-circle" className={styles.infoIcon} />
            </Tooltip>
          </Label>
        </div>
        {showTriggerTemplate && (
          <Controller
            control={control}
            name="triggerTemplate"
            render={({ field }) => (
              <>
                <MonacoEditor
                  {...field}
                  data={{}}
                  showLineNumbers={false}
                  monacoOptions={MONACO_READONLY_CONFIG}
                  onChange={field.onChange}
                />
                <Button
                  icon="edit"
                  variant="secondary"
                  className={styles.editTriggerTemplateBtn}
                  onClick={() => {
                    setTemplateToEdit({
                      value: field.value,
                      displayName: 'outgoing webhook',
                      name: field.name,
                    });
                  }}
                />
                {templateToEdit?.['name'] === field.name && (
                  <WebhooksTemplateEditor
                    id={webhookId}
                    handleSubmit={(value) => {
                      field.onChange(value);
                      setTemplateToEdit(undefined);
                    }}
                    onHide={() => setTemplateToEdit(undefined)}
                    template={templateToEdit}
                  />
                )}
              </>
            )}
          />
        )}
      </div>
    </VerticalGroup>
  );
};
