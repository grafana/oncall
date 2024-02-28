import React, { useEffect, useReducer, useRef, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  Input,
  Label,
  RadioButtonGroup,
  Select,
  Switch,
  TextArea,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { noop } from 'lodash';
import { observer } from 'mobx-react';
import { Control, Controller, FieldErrors, UseFormGetValues, UseFormSetValue, useForm } from 'react-hook-form';
import { useHistory } from 'react-router-dom';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { GSelect } from 'containers/GSelect/GSelect';
import styles from 'containers/IntegrationForm/HookForm.module.scss';
import { Labels } from 'containers/Labels/Labels';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IntegrationHelper } from 'pages/integration/Integration.helper';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { PLUGIN_ROOT, generateAssignToTeamInputDescription } from 'utils/consts';

import { HowTheIntegrationWorks } from './HowTheIntegrationWorks';
import { prepareForEdit } from './IntegrationForm.helpers';

const cx = cn.bind(styles);

interface Field {
  name: string;
  label: string;
  placeholder?: string;
  description?: string;
  required?: string;
  type: FieldType;
}

enum FieldType {
  Input = 'input',
  TextArea = 'textarea',
}

enum FormFieldKeys {
  Name = 'verbal_name',
  Description = 'description_short',
  Team = 'team',
  AlertManager = 'alert_manager',
  ContactPoint = 'contact_point',
  IsExisting = 'is_existing',
  Alerting = 'alerting',
  Integration = 'integration',

  ServiceNowUrl = 'servicenow_url',
  AuthUsername = 'auth_username',
  AuthPassword = 'auth_password',
}

interface FormFields {
  [FormFieldKeys.Name]: string;
  [FormFieldKeys.Description]: string;
  [FormFieldKeys.Team]: string;
  [FormFieldKeys.IsExisting]: boolean;
  [FormFieldKeys.AlertManager]: string;
  [FormFieldKeys.ContactPoint]: string;
  [FormFieldKeys.Alerting]: string;
  [FormFieldKeys.ServiceNowUrl]: string;
  [FormFieldKeys.AuthUsername]: string;
  [FormFieldKeys.AuthPassword]: string;
  [FormFieldKeys.Integration]: string;
}

interface HookFormProps {
  id: ApiSchemas['AlertReceiveChannel']['id'] | 'new';
  isTableView?: boolean;
  selectedIntegration: ApiSchemas['AlertReceiveChannelIntegrationOptions'];
  onBackClick: () => void;
  navigateToAlertGroupLabels: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
  onSubmit: () => Promise<void>;
  onHide: () => void;
}

const radioOptions = [
  {
    label: 'Connect existing Contact point',
    value: 'existing',
  },
  {
    label: 'Create a new one',
    value: 'new',
  },
];

export const HookForm = observer(
  ({
    id,
    isTableView,
    navigateToAlertGroupLabels,
    selectedIntegration,
    onSubmit,
    onHide,
    onBackClick,
  }: HookFormProps) => {
    const {
      control,
      handleSubmit,
      getValues,
      setValue,
      formState: { errors },
    } = useForm<FormFields>({
      defaultValues: {
        [FormFieldKeys.Integration]: selectedIntegration.value,
      },
      mode: 'all',
    });

    const store = useStore();
    const history = useHistory();
    const { userStore, grafanaTeamStore, alertReceiveChannelStore } = store;

    const [
      {
        isExistingContactPoint,
        dataSources,
        contactPoints,
        selectedAlertManagerOption,
        selectedContactPointOption,
        allContactPoints,
      },
      setState,
    ] = useReducer(
      (state: GrafanaContactPointState, newState: Partial<GrafanaContactPointState>) => ({
        ...state,
        ...newState,
      }),
      {
        isExistingContactPoint: true,
        selectedAlertManagerOption: undefined,
        selectedContactPointOption: undefined,
        dataSources: [],
        contactPoints: [],
        allContactPoints: [],
      }
    );

    useEffect(() => {
      (async function () {
        setState({
          allContactPoints: await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints(),
        });
      })();
    }, []);

    const labelsRef = useRef(null);

    const data =
      id === 'new'
        ? { integration: selectedIntegration?.value, team: userStore.currentUser?.current_team, labels: [] }
        : prepareForEdit(alertReceiveChannelStore.items[id]);

    const [labelsErrors, setLabelErrors] = useState([]);
    const isServiceNow = selectedIntegration.value === 'servicenow';
    const isGrafanaAlerting = IntegrationHelper.isSpecificIntegration(selectedIntegration.value, 'grafana_alerting');

    return (
      <form onSubmit={handleSubmit(onFormSubmit)} className={cx('form')}>
        <Controller
          name={FormFieldKeys.Name}
          control={control}
          rules={{ required: 'Name is required' }}
          render={({ field }) => (
            <Field
              key={'Name'}
              label={'Integration Name'}
              placeholder={'Integration Name'}
              invalid={!!errors[FormFieldKeys.Name]}
              error={errors[FormFieldKeys.Name]?.message as string}
            >
              <Input {...field} />
            </Field>
          )}
        />

        <Controller
          name={FormFieldKeys.Description}
          control={control}
          rules={{ required: 'Description is required' }}
          render={({ field }) => (
            <Field
              key={'Description'}
              label={'Integration Description'}
              placeholder={'Integration Name'}
              invalid={!!errors[FormFieldKeys.Description]}
              error={errors[FormFieldKeys.Description]?.message as string}
            >
              {/* TOOD: need to figure out bug on hover from grafana */}
              <TextArea {...field} className={cx('textarea')} />
            </Field>
          )}
        />

        <Controller
          name={FormFieldKeys.Team}
          control={control}
          rules={{ required: false }}
          render={({ field }) => (
            <Field
              key="Team"
              label={
                <Label>
                  <span>Assign to team</span>&nbsp;
                  <Tooltip content={generateAssignToTeamInputDescription('Integrations')} placement="right">
                    <Icon name="info-circle" />
                  </Tooltip>
                </Label>
              }
              invalid={!!errors[FormFieldKeys.Team]}
              error={errors[FormFieldKeys.Team]?.message as string}
            >
              <GSelect
                placeholder="Assign to team"
                {...field}
                {...{
                  items: grafanaTeamStore.items,
                  fetchItemsFn: grafanaTeamStore.updateItems,
                  getSearchResult: grafanaTeamStore.getSearchResult,
                  displayField: 'name',
                  valueField: 'id',
                  showSearch: true,
                  allowClear: true,
                }}
                onChange={(value) => {
                  field.onChange(value);
                }}
              />
            </Field>
          )}
        />

        <RenderConditionally shouldRender={isGrafanaAlerting}>
          <GrafanaContactPoint
            radioOptions={radioOptions}
            isExistingContactPoint={isExistingContactPoint}
            dataSources={dataSources}
            contactPoints={contactPoints}
            selectedAlertManagerOption={selectedAlertManagerOption}
            selectedContactPointOption={selectedContactPointOption}
            allContactPoints={allContactPoints}
            control={control}
            getValues={getValues}
            setValue={setValue}
            setState={setState}
            errors={errors}
          />
        </RenderConditionally>

        {store.hasFeature(AppFeature.Labels) && (
          <div className={cx('labels')}>
            <Labels
              ref={labelsRef}
              errors={labelsErrors}
              value={data.labels}
              description={
                <>
                  Labels{id === 'new' ? ' will be ' : ' '}applied to the integration and inherited by alert groups.
                  <br />
                  You can modify behaviour in{' '}
                  {id === 'new' ? (
                    'Alert group labeling'
                  ) : (
                    <PluginLink onClick={() => navigateToAlertGroupLabels(id)}>Alert group labeling</PluginLink>
                  )}{' '}
                  drawer.
                </>
              }
            />
          </div>
        )}

        {isTableView && <HowTheIntegrationWorks selectedOption={selectedIntegration} />}

        <RenderConditionally shouldRender={isServiceNow}>
          <div className={cx('servicenow-heading')}>
            <Text type="primary">ServiceNow configuration</Text>
          </div>
        </RenderConditionally>

        <RenderConditionally shouldRender={isServiceNow}>
          <Controller
            name={FormFieldKeys.ServiceNowUrl}
            control={control}
            rules={{ required: 'Instance URL is required' }}
            render={({ field }) => (
              <Field
                key={'InstanceURL'}
                label={'Instance URL'}
                invalid={!!errors[FormFieldKeys.ServiceNowUrl]}
                error={errors[FormFieldKeys.ServiceNowUrl]?.message as string}
              >
                <Input {...field} />
              </Field>
            )}
          />
        </RenderConditionally>

        <RenderConditionally shouldRender={isServiceNow}>
          <Controller
            name={FormFieldKeys.AuthUsername}
            control={control}
            rules={{ required: 'Username is required' }}
            render={({ field }) => (
              <Field
                key={'AuthUsername'}
                label={'Username'}
                invalid={!!errors[FormFieldKeys.AuthUsername]}
                error={errors[FormFieldKeys.AuthPassword]?.message as string}
              >
                <Input {...field} />
              </Field>
            )}
          />
        </RenderConditionally>

        <RenderConditionally shouldRender={isServiceNow}>
          <Controller
            name={FormFieldKeys.AuthPassword}
            control={control}
            rules={{ required: 'Password is required' }}
            render={({ field }) => (
              <Field
                key={'InstanceURL'}
                label={'Instance URL'}
                invalid={!!errors[FormFieldKeys.ServiceNowUrl]}
                error={errors[FormFieldKeys.ServiceNowUrl]?.message as string}
              >
                <Input {...field} type="password" />
              </Field>
            )}
          />
        </RenderConditionally>

        <RenderConditionally shouldRender={isServiceNow}>
          <Button className={cx('webhook-test')} variant="secondary" onClick={onWebhookTestClick}>
            Test
          </Button>
        </RenderConditionally>

        <RenderConditionally shouldRender={isServiceNow}>
          <div className={cx('webhook-switch')}>
            <Switch value={true} onChange={noop} />
            <Text type="primary"> Create default outgoing webhook events</Text>
          </div>
        </RenderConditionally>

        <div>
          <HorizontalGroup justify="flex-end">
            {id === 'new' ? (
              <Button variant="secondary" onClick={onBackClick}>
                Back
              </Button>
            ) : (
              <Button variant="secondary" onClick={onHide}>
                Cancel
              </Button>
            )}

            <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
              <Button type="submit" data-testid="update-integration-button">
                {id === 'new' ? 'Create' : 'Update'} Integration
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </div>
      </form>
    );

    async function onWebhookTestClick(): Promise<void> {}

    async function onFormSubmit(formData): Promise<void> {
      const labels = labelsRef.current?.getValue();
      const data = { ...formData, labels };
      const isCreate = id === 'new';

      try {
        if (isCreate) {
          await createNewIntegration();
        } else {
          await alertReceiveChannelStore.update({ id, data, skipErrorHandling: true });
        }
      } catch (error) {
        if (error.labels) {
          setLabelErrors(error.labels);
        }

        return;
      }

      await onSubmit();
      onHide();

      async function createNewIntegration(): Promise<void | ApiSchemas['AlertReceiveChannel']> {
        const response = await alertReceiveChannelStore.create({ data, skipErrorHandling: true });
        const pushHistory = (id: ApiSchemas['AlertReceiveChannel']['id']) =>
          history.push(`${PLUGIN_ROOT}/integrations/${id}`);
        if (!response) {
          return;
        }

        if (!IntegrationHelper.isSpecificIntegration(selectedIntegration.value, 'grafana_alerting')) {
          pushHistory(response.id);
        }

        await (data.is_existing
          ? AlertReceiveChannelHelper.connectContactPoint
          : AlertReceiveChannelHelper.createContactPoint)(response.id, data.alert_manager, data.contact_point);

        pushHistory(response.id);
      }
    }
  }
);

interface ContactPoint {
  name: string;
  uid: string;
  contact_points: string[];
}

interface GrafanaContactPointState {
  isExistingContactPoint: boolean;
  selectedAlertManagerOption: string;
  selectedContactPointOption: string;

  dataSources: Array<{ label: string; value: string }>;
  contactPoints: Array<{ label: string; value: string }>;
  allContactPoints: ContactPoint[];
}

interface GrafanaContactPointProps {
  control: Control<FormFields, any, FormFields>;
  errors: FieldErrors;
  getValues: UseFormGetValues<FormFields>;
  setValue: UseFormSetValue<FormFields>;

  isExistingContactPoint: any;
  dataSources: any;
  contactPoints: any;
  selectedAlertManagerOption: any;
  selectedContactPointOption: any;
  allContactPoints: ContactPoint[];
  radioOptions: Array<{
    label: string;
    value: string;
  }>;

  setState: React.Dispatch<Partial<GrafanaContactPointState>>;
}

const GrafanaContactPoint = observer(
  ({
    allContactPoints,
    radioOptions,
    contactPoints,
    selectedContactPointOption,
    selectedAlertManagerOption,
    isExistingContactPoint,
    dataSources,
    control,
    errors,
    getValues,
    setValue,
    setState,
  }: GrafanaContactPointProps) => {
    useEffect(() => {
      (async function () {
        const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();

        setState({
          allContactPoints: response,
          dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
          contactPoints: [],
        });
      })();

      setValue(FormFieldKeys.IsExisting, true);
    }, []);

    return (
      <div className={cx('extra-fields')}>
        <VerticalGroup spacing="md">
          <HorizontalGroup spacing="xs" align="center">
            <Text type="primary" size="small">
              Grafana Alerting Contact point
            </Text>
            <Icon name="info-circle" />
          </HorizontalGroup>

          <div className={cx('extra-fields__radio')}>
            <Controller
              name={FormFieldKeys.IsExisting}
              control={control}
              render={({ field }) => (
                <RadioButtonGroup
                  {...field}
                  options={radioOptions}
                  value={isExistingContactPoint ? 'existing' : 'new'}
                  onChange={(radioValue) => {
                    setState({
                      isExistingContactPoint: radioValue === 'existing',
                      contactPoints: [],
                      selectedAlertManagerOption: null,
                      selectedContactPointOption: null,
                    });

                    setValue(FormFieldKeys.IsExisting, radioValue === 'existing');
                    setValue(FormFieldKeys.AlertManager, undefined);
                    setValue(FormFieldKeys.ContactPoint, undefined);
                  }}
                />
              )}
            />
          </div>

          <div className={cx('selectors-container')}>
            <Controller
              name={FormFieldKeys.AlertManager}
              control={control}
              rules={{ required: 'Alert Manager is required' }}
              render={({ field }) => (
                <Field
                  key={'AlertManager'}
                  placeholder={'Integration Name'}
                  invalid={!!errors[FormFieldKeys.AlertManager]}
                  error={errors[FormFieldKeys.AlertManager]?.message as string}
                >
                  <Select
                    {...field}
                    options={dataSources}
                    onChange={onAlertManagerChange}
                    value={selectedAlertManagerOption}
                    placeholder="Select Alert Manager"
                  />
                </Field>
              )}
            />

            <Controller
              name={FormFieldKeys.ContactPoint}
              control={control}
              rules={{ required: 'Contact Point is required', validate: contactPointValidator }}
              render={({ field }) => (
                <Field
                  key={FormFieldKeys.ContactPoint}
                  placeholder="Select Contact Point"
                  invalid={!!errors[FormFieldKeys.ContactPoint]}
                  error={errors[FormFieldKeys.ContactPoint]?.message as string}
                >
                  {isExistingContactPoint ? (
                    <Select
                      {...field}
                      options={contactPoints}
                      onChange={onContactPointChange}
                      value={selectedContactPointOption}
                      placeholder="Select Contact Point"
                    />
                  ) : (
                    <Input
                      value={selectedContactPointOption}
                      placeholder="Choose Contact Point"
                      onChange={({ target }) => {
                        const value = (target as HTMLInputElement).value;
                        setState({ selectedContactPointOption: value });
                        setValue(FormFieldKeys.ContactPoint, value, { shouldValidate: true });
                      }}
                    />
                  )}
                </Field>
              )}
            />
          </div>
        </VerticalGroup>
      </div>
    );

    function contactPointValidator(contactPointInputValue: string) {
      const alertManager = getValues(FormFieldKeys.AlertManager);
      const isExisting = getValues(FormFieldKeys.IsExisting);

      const matchingAlertManager = allContactPoints.find((cp) => cp.uid === alertManager);
      const hasContactPointInput = alertManager && contactPointInputValue;

      if (
        !isExisting &&
        hasContactPointInput &&
        matchingAlertManager?.contact_points.find((cp) => cp === contactPointInputValue)
      ) {
        return 'A contact point already exists for this data source';
      }

      return true;
    }

    function onAlertManagerChange(option: SelectableValue<string>) {
      // filter contact points for current alert manager
      const contactPointsForCurrentOption = allContactPoints
        .find((opt) => opt.uid === option.value)
        .contact_points?.map((cp) => ({ value: cp, label: cp }));

      const newState: Partial<GrafanaContactPointState> = {
        selectedAlertManagerOption: option.value,
        contactPoints: contactPointsForCurrentOption,
      };

      if (isExistingContactPoint) {
        newState.selectedContactPointOption = null;
        setValue(FormFieldKeys.ContactPoint, undefined);
      }

      setState(newState);
      setValue(FormFieldKeys.AlertManager, option.value, { shouldValidate: true });
    }

    function onContactPointChange(option: SelectableValue<string>) {
      setState({ selectedContactPointOption: option.value });
      setValue(FormFieldKeys.ContactPoint, option.value, { shouldValidate: true });
    }
  }
);
