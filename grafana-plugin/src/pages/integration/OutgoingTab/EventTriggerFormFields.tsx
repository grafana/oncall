import React, { FC, useState } from 'react';

import { Button, Field, Icon, Label, Select, Switch, Tooltip, useStyles2, VerticalGroup } from '@grafana/ui';
import { Controller, useFormContext } from 'react-hook-form';

import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { WebhooksTemplateEditor } from 'containers/WebhooksTemplateEditor/WebhooksTemplateEditor';
import { WEBHOOK_TRIGGGER_TYPE_OPTIONS } from 'models/outgoing_webhook/outgoing_webhook.types';

import { getStyles } from './OutgoingTab.styles';
import { FormValues } from './OutgoingTab.types';

interface TemplateToEdit {
  value: string;
  displayName: string;
  name: string;
}

interface EventTriggerFormFieldsProps {
  // "new" should be used for new event trigger
  webhookId: string;
}

export const EventTriggerFormFields: FC<EventTriggerFormFieldsProps> = ({ webhookId }) => {
  const styles = useStyles2(getStyles);
  const { control, watch } = useFormContext<FormValues>();
  const [templateToEdit, setTemplateToEdit] = useState<TemplateToEdit>();

  const isEditingExistingWebhook = webhookId !== 'new';

  const [showTriggerTemplate, showForwardedDataTemplate] = watch([
    'triggerTemplateToogle',
    'forwardedDataTemplateToogle',
  ]);

  return (
    <VerticalGroup spacing="lg">
      <Field
        key="triggerType"
        label={
          <Label>
            <span>Event trigger type</span>&nbsp;
            <Tooltip content="Some description" placement="right">
              <Icon name="info-circle" className={styles.infoIcon} />
            </Tooltip>
          </Label>
        }
        className={styles.selectField}
      >
        <Controller
          control={control}
          name="triggerType"
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
      {isEditingExistingWebhook && (
        <div className={styles.switcherFieldWrapper}>
          <Controller
            control={control}
            name="isEnabled"
            render={({ field: { value, onChange } }) => <Switch value={value} onChange={() => onChange(!value)} />}
          />
          <Label className={styles.switcherLabel}>Enabled</Label>
        </div>
      )}
      <div className={styles.switcherFieldWrapper}>
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
              <div className={styles.monacoEditorWrapper}>
                <MonacoEditor
                  {...field}
                  data={{}} // TODO:update
                  showLineNumbers={false}
                  monacoOptions={MONACO_READONLY_CONFIG}
                  onChange={field.onChange}
                />
                <Button
                  icon="edit"
                  variant="secondary"
                  onClick={() => {
                    setTemplateToEdit({
                      value: field.value,
                      displayName: 'event trigger',
                      name: field.name,
                    });
                  }}
                />
              </div>
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
      <div className={styles.switcherFieldWrapper}>
        <Controller
          control={control}
          name="forwardedDataTemplateToogle"
          render={({ field: { value, onChange } }) => <Switch value={value} onChange={() => onChange(!value)} />}
        />
        <Label className={styles.switcherLabel}>
          <span>Customise forwarded data template</span>
          <Tooltip content="Some description" placement="right">
            <Icon name="info-circle" className={styles.infoIcon} />
          </Tooltip>
        </Label>
      </div>
      {showForwardedDataTemplate && (
        <Controller
          control={control}
          name="forwardedDataTemplate"
          render={({ field }) => (
            <>
              <div className={styles.monacoEditorWrapper}>
                <MonacoEditor
                  {...field}
                  data={{}} // TODO:update
                  showLineNumbers={false}
                  monacoOptions={MONACO_READONLY_CONFIG}
                  onChange={field.onChange}
                />
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
              </div>
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
    </VerticalGroup>
  );
};
