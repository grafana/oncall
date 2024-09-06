import React from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Field, Input, RadioButtonList, Select, Switch, useStyles2 } from '@grafana/ui';
import { generateAssignToTeamInputDescription } from 'helpers/consts';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { Controller, useFormContext } from 'react-hook-form';

import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { GSelect } from 'containers/GSelect/GSelect';
import { Labels } from 'containers/Labels/Labels';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import {
  HTTP_METHOD_OPTIONS,
  OutgoingWebhookPreset,
  WEBHOOK_TRIGGGER_TYPE_OPTIONS,
} from 'models/outgoing_webhook/outgoing_webhook.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import { getStyles } from './OutgoingWebhookForm.styles';
import { TemplateParams, WebhookFormFieldName } from './OutgoingWebhookForm.types';

interface OutgoingWebhookFormFieldsProps {
  preset: OutgoingWebhookPreset;
  hasLabelsFeature: boolean;
  onTemplateEditClick: (params: TemplateParams) => void;
}

const FORWARD = 'forward';
const CUSTOMIZE = 'customise';
const FORWARD_RADIO_OPTIONS = [
  {
    label: 'Forward whole payload data',
    value: FORWARD,
    boolean: true,
  },
  {
    label: 'Customise forwarded data',
    value: CUSTOMIZE,
    boolean: false,
  },
];

export const OutgoingWebhookFormFields: React.FC<OutgoingWebhookFormFieldsProps> = observer(
  ({ preset, hasLabelsFeature, onTemplateEditClick }) => {
    const {
      grafanaTeamStore,
      // dereferencing items is needed to rerender GSelect
      grafanaTeamStore: { items: grafanaTeamItems },
      alertReceiveChannelStore,
    } = useStore();
    const { items, fetchItems, fetchItemById } = alertReceiveChannelStore;
    const {
      control,
      formState: { errors },
      watch,
    } = useFormContext<ApiSchemas['Webhook']>();

    const forwardAll = watch(WebhookFormFieldName.ForwardAll);
    const styles = useStyles2(getStyles);

    const controls = (
      <>
        <Controller
          name={WebhookFormFieldName.Name}
          control={control}
          rules={{ required: 'Name is required' }}
          render={({ field }) => (
            <Field label="Name" invalid={Boolean(errors.name)} error={errors.name?.message}>
              <Input name="name" value={field.value} onChange={field.onChange} />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.IsWebhookEnabled}
          control={control}
          render={({ field }) => (
            <Field
              label="Enabled"
              invalid={Boolean(errors.is_webhook_enabled)}
              error={errors.is_webhook_enabled?.message}
            >
              <Switch value={field.value} onChange={field.onChange} />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.Team}
          control={control}
          render={({ field }) => (
            <Field
              label="Assign to team"
              description={`${generateAssignToTeamInputDescription(
                'Outgoing Webhooks'
              )} This setting does not effect execution of the webhook.`}
              invalid={!!errors.team}
              error={errors.team?.message}
            >
              <GSelect<GrafanaTeam>
                allowClear
                items={grafanaTeamItems}
                fetchItemsFn={grafanaTeamStore.updateItems}
                fetchItemFn={grafanaTeamStore.fetchItemById}
                getSearchResult={grafanaTeamStore.getSearchResult}
                displayField="name"
                valueField="id"
                placeholder="Choose (Optional)"
                value={field.value}
                onChange={field.onChange}
                dataTestId="team-selector"
              />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.TriggerType}
          control={control}
          rules={{ required: 'Trigger Type is required' }}
          render={({ field }) => (
            <Field
              label="Trigger Type"
              description="The type of event which will cause this webhook to execute."
              invalid={!!errors.trigger_type}
              error={errors.trigger_type?.message}
            >
              <Select
                data-testid="triggerType-selector"
                placeholder="Choose (Required)"
                value={field.value}
                menuShouldPortal
                options={WEBHOOK_TRIGGGER_TYPE_OPTIONS}
                onChange={({ value }) => field.onChange(value)}
              />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.HttpMethod}
          control={control}
          rules={{ required: 'HTTP Method is required' }}
          render={({ field }) => (
            <Field label="HTTP Method" invalid={!!errors.http_method} error={errors.http_method?.message}>
              <Select
                placeholder="Choose (Required)"
                value={field.value}
                menuShouldPortal
                options={HTTP_METHOD_OPTIONS}
                onChange={({ value }) => field.onChange(value)}
              />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.IntegrationFilter}
          control={control}
          render={({ field }) => (
            <Field
              label="Integrations"
              description="Integrations that this webhook applies to. If this is empty the webhook will execute for all integrations"
              invalid={!!errors.integration_filter}
              error={errors.integration_filter?.message}
            >
              <GSelect<ApiSchemas['AlertReceiveChannel']>
                isMulti
                placeholder="Choose (Optional)"
                items={items}
                fetchItemsFn={fetchItems}
                fetchItemFn={fetchItemById}
                getSearchResult={() => AlertReceiveChannelHelper.getSearchResult(alertReceiveChannelStore)}
                displayField="verbal_name"
                valueField="id"
                getOptionLabel={(item: SelectableValue) => <Emoji text={item?.label || ''} />}
                value={field.value}
                onChange={field.onChange}
              />
            </Field>
          )}
        />
        {hasLabelsFeature && (
          <Controller
            name={WebhookFormFieldName.Labels}
            control={control}
            render={({ field }) => (
              <Labels
                value={field.value}
                errors={errors.labels}
                onDataUpdate={field.onChange}
                description="Labels applied to the webhook will be included in the webhook payload, along with alert group and integration labels."
              />
            )}
          />
        )}
        <Controller
          rules={{ required: 'Webhook URL is required' }}
          name={WebhookFormFieldName.Url}
          control={control}
          render={({ field }) => (
            <Field label="Webhook URL" invalid={!!errors.url} error={errors.url?.message}>
              <div className={styles.formRow}>
                <div className={styles.formField}>
                  <MonacoEditor
                    data={{}}
                    height={30}
                    showLineNumbers={false}
                    monacoOptions={MONACO_EDITABLE_CONFIG}
                    value={field.value}
                    onChange={field.onChange}
                  />
                </div>
                <Button
                  icon="edit"
                  variant="secondary"
                  onClick={() =>
                    onTemplateEditClick({
                      name: field.name,
                      value: field.value,
                      displayName: 'Webhook URL',
                    })
                  }
                />
              </div>
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.Headers}
          control={control}
          render={({ field }) => (
            <Field label="Webhook Headers" description="Request headers should be in JSON format.">
              <div className={styles.formRow}>
                <div className={styles.formField}>
                  <MonacoEditor
                    data={{}}
                    showLineNumbers={false}
                    monacoOptions={MONACO_EDITABLE_CONFIG}
                    value={field.value}
                    onChange={field.onChange}
                  />
                </div>
                <Button
                  icon="edit"
                  variant="secondary"
                  onClick={() =>
                    onTemplateEditClick({
                      name: field.name,
                      value: field.value,
                      displayName: 'Webhook Headers',
                    })
                  }
                />
              </div>
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.Username}
          control={control}
          render={({ field }) => (
            <Field label="Username" invalid={Boolean(errors.username)} error={errors.username?.message}>
              <Input value={field.value} onChange={field.onChange} />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.Password}
          control={control}
          render={({ field }) => (
            <Field label="Password" invalid={Boolean(errors.password)} error={errors.password?.message}>
              <Input type="password" value={field.value} onChange={field.onChange} />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.AuthorizationHeader}
          control={control}
          render={({ field }) => (
            <Field
              label="Authorization Header"
              invalid={Boolean(errors.authorization_header)}
              error={errors.authorization_header?.message}
            >
              <Input type="password" value={field.value} onChange={field.onChange} />
            </Field>
          )}
        />
        <Controller
          name={WebhookFormFieldName.TriggerTemplate}
          control={control}
          render={({ field }) => (
            <Field
              label="Trigger Template"
              description="Trigger template is used to conditionally execute the webhook based on incoming data. The trigger template must be empty or evaluate to true or 1 for the webhook to be sent"
            >
              <div className={styles.formRow}>
                <div className={styles.formField}>
                  <MonacoEditor
                    data={{}}
                    showLineNumbers={false}
                    monacoOptions={MONACO_EDITABLE_CONFIG}
                    value={field.value}
                    onChange={field.onChange}
                  />
                </div>
                <Button
                  icon="edit"
                  variant="secondary"
                  onClick={() =>
                    onTemplateEditClick({
                      name: field.name,
                      value: field.value,
                      displayName: 'Webhook Trigger Template',
                    })
                  }
                />
              </div>
            </Field>
          )}
        />

        <RenderConditionally shouldRender={!preset?.controlled_fields.includes(WebhookFormFieldName.ForwardAll)}>
          <Field>
            <Controller
              name={WebhookFormFieldName.ForwardAll}
              control={control}
              render={({ field }) => (
                <RadioButtonList
                  name="forwardData"
                  options={FORWARD_RADIO_OPTIONS}
                  value={FORWARD_RADIO_OPTIONS.find((opt) => opt.boolean === field.value)?.value}
                  onChange={(value) => field.onChange(value === FORWARD)}
                />
              )}
            />
          </Field>

          <RenderConditionally
            shouldRender={!forwardAll}
            render={() => (
              <Controller
                name={WebhookFormFieldName.Data}
                rules={{ required: 'Data is required' }}
                control={control}
                render={({ field }) => (
                  <Field
                    label="Data"
                    invalid={Boolean(errors.data)}
                    error={errors.data?.message}
                    description={`Available variables: {{ event }}, {{ user }}, {{ alert_group }}, {{ alert_group_id }}, {{ alert_payload }}, {{ integration }}, {{ notified_users }}, {{ users_to_be_notified }}, {{ responses }}${
                      hasLabelsFeature ? ' {{ webhook }}' : ''
                    }`}
                  >
                    <div className={styles.formRow}>
                      <div className={styles.formField}>
                        <MonacoEditor
                          data={{}}
                          showLineNumbers={false}
                          monacoOptions={{ ...MONACO_EDITABLE_CONFIG }}
                          value={field.value}
                          onChange={field.onChange}
                        />
                      </div>
                      <Button
                        icon="edit"
                        variant="secondary"
                        onClick={() =>
                          onTemplateEditClick({
                            name: field.name,
                            value: field.value,
                            displayName: 'Webhook Data',
                          })
                        }
                      />
                    </div>
                  </Field>
                )}
              />
            )}
          />
        </RenderConditionally>
      </>
    );

    return (
      <>
        {React.Children.toArray(controls.props.children).filter(
          (child) => !preset?.controlled_fields.includes((child as React.ReactElement).props.name)
        )}
      </>
    );
  }
);
