import cn from 'classnames/bind';
import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  Input,
  Label,
  RadioButtonGroup,
  Select,
  TextArea,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import React, { useEffect, useReducer, useRef, useState } from 'react';
import {
  Control,
  Controller,
  FieldError,
  FieldErrors,
  UseFormGetValues,
  UseFormSetValue,
  useForm,
} from 'react-hook-form';

import styles from 'containers/IntegrationForm/HookForm.module.scss';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization/authorization';
import { generateAssignToTeamInputDescription } from 'utils/consts';
import { GSelect } from 'containers/GSelect/GSelect';
import { useStore } from 'state/useStore';
import { observer } from 'mobx-react';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { Text } from 'components/Text/Text';
import { SelectableValue } from '@grafana/data';
import { AppFeature } from 'state/features';
import { Labels } from 'containers/Labels/Labels';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { ApiSchemas } from 'network/oncall-api/api.types';
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

enum FieldKey {
  Name = 'Name',
}

const fields: { [key in FieldKey]: Field } = {
  [FieldKey.Name]: {
    name: 'name',
    label: 'Name',
    placeholder: 'Integration Name',
    type: FieldType.Input,
    required: 'Integration Name is required',
  },
};

interface HookFormProps {
  navigateToAlertGroupLabels: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
}

export const HookForm = observer(({ navigateToAlertGroupLabels }: HookFormProps) => {
  const {
    control,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm(); // add { formValues } if def values needed

  const store = useStore();
  const { userStore, grafanaTeamStore, alertReceiveChannelStore } = store;

  const [selectedOption, setSelectedOption] = useState<ApiSchemas['AlertReceiveChannelIntegrationOptions']>(undefined);

  const labelsRef = useRef(null);

  const id = 'new';

  const data =
    id === 'new'
      ? { integration: selectedOption?.value, team: userStore.currentUser?.current_team, labels: [] }
      : prepareForEdit(alertReceiveChannelStore.items[id]);

  console.log(getValues());

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className={cx('form')}>
      <Controller
        name={'Name'}
        control={control}
        rules={{ required: 'Name is required' }}
        render={({ field }) => (
          <Field
            key={'Name'}
            label={'Integration Name'}
            placeholder={'Integration Name'}
            invalid={!!errors['Name']}
            error={errors['Name']?.message as string}
          >
            <Input {...field} />
          </Field>
        )}
      />

      <Controller
        name={'Description'}
        control={control}
        rules={{ required: 'Description is required' }}
        render={({ field }) => (
          <Field
            key={'Description'}
            label={'Integration Description'}
            placeholder={'Integration Name'}
            invalid={!!errors['Description']}
            error={errors['Description']?.message as string}
          >
            <TextArea {...field} />
          </Field>
        )}
      />

      <Controller
        name={'AssignToTeam'}
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
            invalid={!!errors['Team']}
            error={errors['Team']?.message as string}
          >
            <GSelect
              isMulti={true}
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
              onChange={(value) => field.onChange(value)}
            />
          </Field>
        )}
      />

      <GrafanaContactPoint control={control} getValues={getValues} setValue={setValue} errors={errors} />

      {store.hasFeature(AppFeature.Labels) && (
        <div className={cx('labels')}>
          <Labels
            ref={labelsRef}
            errors={errors?.labels}
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

      <div>
        <HorizontalGroup justify="flex-end">
          {id === 'new' ? (
            <Button variant="secondary" onClick={() => console.log('click')}>
              Back
            </Button>
          ) : (
            <Button variant="secondary" onClick={() => console.log('click')}>
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

  function onFormSubmit(data) {
    console.log({ data });
  }
});

interface GrafanaContactPointState {
  isExistingContactPoint: boolean;
  selectedAlertManagerOption: string;
  selectedContactPointOption: string;

  dataSources: Array<{ label: string; value: string }>;
  contactPoints: Array<{ label: string; value: string }>;
  allContactPoints: Array<{ name: string; uid: string; contact_points: string[] }>;
}

interface GrafanaContactPointProps {
  control: Control;
  errors: FieldErrors;
  // TODO: add interface typing
  getValues: UseFormGetValues<any>;
  setValue: UseFormSetValue<any>;
}

const GrafanaContactPoint = observer(({ control, errors, getValues, setValue }: GrafanaContactPointProps) => {
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

  console.log({ contactPoints });

  useEffect(() => {
    (async function () {
      const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();

      setState({
        allContactPoints: response,
        dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
        contactPoints: [],
      });
    })();

    setValue('IsExisting', true);
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
            name={'IsExisting'}
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

                  setValue('IsExisting', radioValue === 'existing');
                  setValue('AlertManager', undefined);
                  setValue('ContactPoint', undefined);
                }}
              />
            )}
          />
        </div>

        <div className={cx('selectors-container')}>
          <Controller
            name={'AlertManager'}
            control={control}
            rules={{ required: 'Alert Manager is required' }}
            render={({ field }) => (
              <Field
                key={'AlertManager'}
                placeholder={'Integration Name'}
                invalid={!!errors['AlertManager']}
                error={errors['AlertManager']?.message as string}
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
            name={'ContactPoint'}
            control={control}
            rules={{ required: 'Contact Point is required' }}
            render={({ field }) => (
              <Field
                key={'ContactPoint'}
                placeholder="Select Contact Point"
                invalid={!!errors['ContactPoint']}
                error={errors['ContactPoint']?.message as string}
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
                      setValue('ContactPoint', value);
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

  function onAlertManagerChange(option: SelectableValue<string>) {
    const contactPointsForCurrentOption = allContactPoints
      .find((opt) => opt.uid === option.value)
      .contact_points?.map((cp) => ({ value: cp, label: cp }));

    const newState: Partial<GrafanaContactPointState> = {
      selectedAlertManagerOption: option.value,
      contactPoints: contactPointsForCurrentOption,
    };

    if (isExistingContactPoint) {
      newState.selectedContactPointOption = null;
      setValue('ContactPoint', undefined);
    }

    setState(newState);
    setValue('AlertManager', option.value);
  }

  function onContactPointChange(option: SelectableValue<string>) {
    setState({ selectedContactPointOption: option.value });
    setValue('ContactPoint', option.value);
  }
});
