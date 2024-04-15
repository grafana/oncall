import React, { FC, useState } from 'react';

import { Button, Field, HorizontalGroup, Label, Select, Switch, useStyles2, VerticalGroup } from '@grafana/ui';
import cn from 'classnames';
import { Controller, useFormContext } from 'react-hook-form';

import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG, MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
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
  const { control, watch, formState } = useFormContext<OutgoingTabFormValues>();
  const [templateToEdit, setTemplateToEdit] = useState<TemplateToEdit>();

  const [showTriggerTemplate] = watch(['triggerTemplateToogle']);

  return (
    <VerticalGroup spacing="lg">
      <div className={styles.switcherFieldWrapper}>
        <Controller
          control={control}
          name="is_webhook_enabled"
          render={({ field: { value, onChange } }) => <Switch value={value} onChange={() => onChange(!value)} />}
        />
        <Label className={styles.switcherLabel}>Enabled</Label>
      </div>
      <Controller
        control={control}
        name="trigger_type"
        rules={{
          required: 'Trigger type is required',
        }}
        render={({ field }) => (
          <Field
            key="trigger_type"
            invalid={Boolean(formState.errors.trigger_type)}
            error={formState.errors.trigger_type?.message}
            label={
              <Label>
                <span>Trigger type</span>
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
      <Controller
        control={control}
        name="http_method"
        rules={{
          required: 'HTTP method is required',
        }}
        render={({ field }) => (
          <Field
            key="http_method"
            invalid={Boolean(formState.errors.http_method)}
            error={formState.errors.http_method?.message}
            label={
              <Label>
                <span>HTTP method</span>
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
        name="url"
        render={({ field }) => (
          <VerticalGroup>
            <HorizontalGroup width="100%" justify="space-between">
              <Label>
                <span>Webhook URL</span>
              </Label>
              <Button
                icon="edit"
                variant="secondary"
                onClick={() => {
                  setTemplateToEdit({
                    value: field.value,
                    displayName: 'webhook url',
                    name: field.name,
                  });
                }}
              />
            </HorizontalGroup>
            <MonacoEditor
              {...field}
              data={{}} // TODO:update
              showLineNumbers={false}
              height={30}
              monacoOptions={MONACO_EDITABLE_CONFIG}
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
      <Controller
        control={control}
        name="data"
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
          </Label>
        </div>
        {showTriggerTemplate && (
          <Controller
            control={control}
            name="trigger_template"
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
