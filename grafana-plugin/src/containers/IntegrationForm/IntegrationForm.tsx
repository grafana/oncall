import React, { useEffect, useReducer, useRef, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  Input,
  Label,
  LoadingPlaceholder,
  RadioButtonGroup,
  Select,
  Switch,
  TextArea,
  Tooltip,
  VerticalGroup,
  useStyles2,
} from '@grafana/ui';
import { observer } from 'mobx-react';
import { parseUrl } from 'query-string';
import { Controller, useForm, useFormContext, FormProvider } from 'react-hook-form';
import { useHistory } from 'react-router-dom';

import { HowTheIntegrationWorks } from 'components/HowTheIntegrationWorks/HowTheIntegrationWorks';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { GSelect } from 'containers/GSelect/GSelect';
import { Labels } from 'containers/Labels/Labels';
import { ServiceNowAuthSection } from 'containers/ServiceNowConfigDrawer/ServiceNowAuthSection';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IntegrationHelper, getIsBidirectionalIntegration } from 'pages/integration/Integration.helper';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { PLUGIN_ROOT, generateAssignToTeamInputDescription, DOCS_ROOT, INTEGRATION_SERVICENOW } from 'utils/consts';
import { useIsLoading } from 'utils/hooks';
import { OmitReadonlyMembers } from 'utils/types';

import { prepareForEdit } from './IntegrationForm.helpers';
import { getIntegrationFormStyles } from './IntegrationForm.styles';

export interface IntegrationFormFields {
  verbal_name?: string;
  description_short?: string;
  team?: string;
  is_existing?: boolean;
  alert_manager?: string;
  contact_point?: string;
  integration: ApiSchemas['AlertReceiveChannel']['integration'];
  create_default_webhooks: boolean;

  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

interface AuthSection {
  testConnection(): Promise<boolean>;
}

interface IntegrationFormProps {
  id: ApiSchemas['AlertReceiveChannel']['id'] | 'new';
  isTableView?: boolean;
  selectedIntegration: ApiSchemas['AlertReceiveChannelIntegrationOptions'];
  onBackClick: () => void;
  navigateToAlertGroupLabels: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
  onSubmit: () => Promise<void>;
  onHide: () => void;
}

const RADIO_OPTIONS = [
  {
    label: 'Connect existing Contact point',
    value: 'existing',
  },
  {
    label: 'Create a new one',
    value: 'new',
  },
];

export const IntegrationForm = observer(
  ({
    id,
    isTableView,
    navigateToAlertGroupLabels,
    selectedIntegration,
    onSubmit,
    onHide,
    onBackClick,
  }: IntegrationFormProps) => {
    const store = useStore();
    const history = useHistory();
    const styles = useStyles2(getIntegrationFormStyles);
    const isNew = id === 'new';
    const { userStore, grafanaTeamStore, alertReceiveChannelStore } = store;

    const data: Partial<ApiSchemas['AlertReceiveChannel']> = isNew
      ? {
          integration: selectedIntegration?.value as ApiSchemas['AlertReceiveChannel']['integration'],
          team: userStore.currentUser?.current_team,
          labels: [],
          additional_settings: {
            instance_url: undefined,
            password: undefined,
            username: undefined,
            is_configured: false,
            state_mapping: {
              acknowledged: undefined,
              firing: undefined,
              resolved: undefined,
              silenced: undefined,
            },
          },
        }
      : prepareForEdit(alertReceiveChannelStore.items[id]);

    const { integration } = data;

    const formMethods = useForm<IntegrationFormFields>({
      defaultValues: isNew
        ? {
            // these are the default values for creating an integration
            integration,
            create_default_webhooks: true,
            additional_settings: {},
          }
        : {
            // existing values from existing integration (edit-mode)
            ...data,
          },
      mode: 'onChange',
    });

    const {
      control,
      handleSubmit,
      formState: { errors },
    } = formMethods;

    const isLoading = useIsLoading(ActionKey.UPDATE_INTEGRATION);

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
    const authSectionRef = useRef<AuthSection>(null);

    const [labelsErrors, setLabelErrors] = useState([]);
    const isServiceNow = getIsBidirectionalIntegration(data as Partial<ApiSchemas['AlertReceiveChannel']>);
    const isGrafanaAlerting = IntegrationHelper.isSpecificIntegration(integration, 'grafana_alerting');

    return (
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onFormSubmit)} className={styles.form}>
          <Controller
            name={'verbal_name'}
            control={control}
            rules={{ required: 'Name is required' }}
            render={({ field }) => (
              <Field
                key={'Name'}
                label={'Integration Name'}
                invalid={!!errors.verbal_name}
                error={errors.verbal_name?.message}
              >
                <Input {...field} placeholder={'Integration Name'} />
              </Field>
            )}
          />

          <Controller
            name={'description_short'}
            control={control}
            render={({ field }) => (
              <Field key={'Description'} label={'Integration Description'}>
                <TextArea {...field} className={styles.textarea} placeholder={'Integration Description'} />
              </Field>
            )}
          />

          <Controller
            name={'team'}
            control={control}
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
                invalid={!!errors.team}
                error={errors.team?.message}
              >
                <GSelect<GrafanaTeam>
                  placeholder="Assign to team"
                  {...field}
                  {...{
                    items: grafanaTeamStore.items,
                    fetchItemsFn: grafanaTeamStore.updateItems,
                    fetchItemFn: grafanaTeamStore.fetchItemById,
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

          <RenderConditionally shouldRender={isGrafanaAlerting && isNew}>
            <GrafanaContactPoint
              radioOptions={RADIO_OPTIONS}
              isExistingContactPoint={isExistingContactPoint}
              dataSources={dataSources}
              contactPoints={contactPoints}
              selectedAlertManagerOption={selectedAlertManagerOption}
              selectedContactPointOption={selectedContactPointOption}
              allContactPoints={allContactPoints}
              setState={setState}
            />
          </RenderConditionally>

          {store.hasFeature(AppFeature.Labels) && (
            <div className={styles.labels}>
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

          <RenderConditionally shouldRender={isServiceNow && isNew}>
            <div className={styles.serviceNowHeading}>
              <HorizontalGroup>
                <Text type="primary">ServiceNow configuration</Text>
              </HorizontalGroup>
              <HorizontalGroup>
                <Text type={'primary'} size={'small'}>
                  Fill in ServiceNow credentials to be used by Grafana OnCall.{' '}
                  <a href={`${DOCS_ROOT}/integrations/servicenow/`} target="_blank" rel="noreferrer">
                    <Text type="link">Read setup guide</Text>
                  </a>
                </Text>
              </HorizontalGroup>
            </div>

            <Controller
              name={'additional_settings.instance_url'}
              control={control}
              rules={{ required: 'Instance URL is required', validate: validateURL }}
              render={({ field }) => (
                <Field
                  key={'InstanceURL'}
                  label={'Instance URL'}
                  invalid={!!errors.additional_settings?.instance_url}
                  error={errors.additional_settings?.instance_url?.message}
                >
                  <Input {...field} />
                </Field>
              )}
            />

            <Controller
              name={'additional_settings.username'}
              control={control}
              rules={{ required: 'Username is required' }}
              render={({ field }) => (
                <Field
                  key={'AuthUsername'}
                  label={'Username'}
                  invalid={!!errors.additional_settings?.username}
                  error={errors.additional_settings?.username?.message}
                >
                  <Input {...field} />
                </Field>
              )}
            />

            <Controller
              name={'additional_settings.password'}
              control={control}
              rules={{ required: 'Password is required' }}
              render={({ field }) => (
                <Field
                  key={'AuthPassword'}
                  label={'Password'}
                  invalid={!!errors.additional_settings?.password}
                  error={errors.additional_settings?.password?.message}
                >
                  <Input {...field} type="password" />
                </Field>
              )}
            />

            <ServiceNowAuthSection ref={authSectionRef} />

            <Controller
              name={'create_default_webhooks'}
              control={control}
              render={({ field }) => (
                <div className={styles.webhookSwitch}>
                  <Switch value={field.value} onChange={field.onChange} />
                  <Text type="primary"> Create default outgoing webhooks</Text>
                  <Tooltip
                    content={
                      <>
                        If enabled, all the necessary webhooks will be created automatically. It's highly recommended to
                        keep this option enabled.
                      </>
                    }
                  >
                    <Icon name={'info-circle'} />
                  </Tooltip>
                </div>
              )}
            />
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
                {renderUpdateIntegrationButton(id)}
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </form>
      </FormProvider>
    );

    function renderUpdateIntegrationButton(id: string) {
      const buttonCopy: string = id === 'new' ? 'Create Integration' : 'Update Integration';

      return (
        <Button type="submit" data-testid="update-integration-button">
          {isLoading ? <LoadingPlaceholder text="Loading..." className={styles.loader} /> : buttonCopy}
        </Button>
      );
    }

    function validateURL(urlFieldValue: string): string | boolean {
      return !parseUrl(urlFieldValue) ? 'Instance URL is invalid' : true;
    }

    async function onFormSubmit(formData: IntegrationFormFields): Promise<void> {
      const labels = labelsRef.current?.getValue();

      const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannelCreate']> = {
        ...formData,
        labels: labels ? [...labels] : undefined,
      };

      const isServiceNow = formData.integration === INTEGRATION_SERVICENOW;

      if (!isServiceNow) {
        delete data.additional_settings;
      }

      if (isServiceNow && isNew) {
        const testResult = await authSectionRef?.current?.testConnection();
        if (!testResult) {
          return;
        }
      }

      try {
        if (isNew) {
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

      async function createNewIntegration(): Promise<void | ApiSchemas['AlertReceiveChannelCreate']> {
        const response = await alertReceiveChannelStore.create({ data, skipErrorHandling: true });
        const pushHistory = (id: ApiSchemas['AlertReceiveChannel']['id']) =>
          history.push(`${PLUGIN_ROOT}/integrations/${id}`);
        if (!response) {
          return;
        }

        if (IntegrationHelper.isSpecificIntegration(selectedIntegration.value, 'grafana_alerting')) {
          await (formData.is_existing
            ? AlertReceiveChannelHelper.connectContactPoint
            : AlertReceiveChannelHelper.createContactPoint)(
            response.id,
            formData.alert_manager,
            formData.contact_point
          );
        }

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
  isExistingContactPoint: any;
  dataSources: any;
  contactPoints: any;
  selectedAlertManagerOption: string;
  selectedContactPointOption: string;
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
    setState,
  }: GrafanaContactPointProps) => {
    const {
      control,
      getValues,
      setValue,
      formState: { errors },
      register,
    } = useFormContext<IntegrationFormFields>();

    useEffect(() => {
      (async function () {
        const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();

        setState({
          allContactPoints: response,
          dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
          contactPoints: [],
        });
      })();

      setValue('is_existing', true);
    }, []);

    const styles = useStyles2(getIntegrationFormStyles);

    return (
      <div className={styles.extraFields}>
        <VerticalGroup spacing="md">
          <HorizontalGroup spacing="xs" align="center">
            <Text type="primary" size="small">
              Grafana Alerting Contact point
            </Text>
            <Icon name="info-circle" />
          </HorizontalGroup>

          <div className={styles.extraFieldsRadio}>
            <Controller
              name={'is_existing'}
              control={control}
              render={({ field }) => (
                <RadioButtonGroup
                  {...field}
                  {...register('is_existing')}
                  options={radioOptions}
                  value={isExistingContactPoint ? 'existing' : 'new'}
                  onChange={(radioValue) => {
                    setState({
                      isExistingContactPoint: radioValue === 'existing',
                      contactPoints: [],
                      selectedAlertManagerOption: null,
                      selectedContactPointOption: null,
                    });

                    setValue('is_existing', radioValue === 'existing');
                    setValue('alert_manager', undefined);
                    setValue('contact_point', undefined);
                  }}
                />
              )}
            />
          </div>

          <div className={styles.selectorsContainer}>
            <Controller
              name={'alert_manager'}
              control={control}
              rules={{ required: 'Alert Manager is required' }}
              render={({ field }) => (
                <Field key={'AlertManager'} invalid={!!errors.alert_manager} error={errors.alert_manager?.message}>
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
              name={'contact_point'}
              control={control}
              rules={{ required: 'Contact Point is required', validate: contactPointValidator }}
              render={({ field }) => (
                <Field key={'contact_point'} invalid={!!errors.contact_point} error={errors.contact_point?.message}>
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
                      onChange={({ currentTarget }) => {
                        const { value } = currentTarget;
                        setState({ selectedContactPointOption: value });
                        setValue('contact_point', value, { shouldValidate: true });
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
      const alertManager = getValues('alert_manager');
      const isExisting = getValues('is_existing');

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
        setValue('contact_point', undefined);
      }

      setState(newState);
      setValue('alert_manager', option.value, { shouldValidate: true });
    }

    function onContactPointChange(option: SelectableValue<string>) {
      setState({ selectedContactPointOption: option.value });
      setValue('contact_point', option.value, { shouldValidate: true });
    }
  }
);
