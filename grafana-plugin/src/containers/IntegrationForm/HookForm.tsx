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
import React, { useEffect, useReducer } from 'react';
import { Control, Controller, FieldError, useForm } from 'react-hook-form';

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

export const HookForm = observer(() => {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm(); // add { formValues } if def values needed

  const store = useStore();
  const { grafanaTeamStore } = store;

  const id = 'new';

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

      <GrafanaContactPoint control={control} errors={errors} />

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
  errors: FieldError;
}

const GrafanaContactPoint = observer(({ control, errors }) => {
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

  useEffect(() => {
    (async function () {
      const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();
      setState({
        allContactPoints: response,
        dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
        contactPoints: [],
      });
    })();

    // TODO: figure out how is this converted
    // setValue('is_existing', true);
  }, []);

  console.log('works');

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
          <RadioButtonGroup
            options={radioOptions}
            value={isExistingContactPoint ? 'existing' : 'new'}
            onChange={(radioValue) => {
              setState({
                isExistingContactPoint: radioValue === 'existing',
                contactPoints: [],
                selectedAlertManagerOption: null,
                selectedContactPointOption: null,
              });

              //   setValue('is_existing', radioValue === 'existing');
              //   setValue('alert_manager', undefined);
              //   setValue('contact_point', undefined);
            }}
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

          {/* <Field invalid={!!errors['alert_manager']} error={'Alert Manager is required'}>
            <Select
              {...register('alert_manager', { required: true })}
              options={dataSources}
              onChange={onAlertManagerChange}
              value={selectedAlertManagerOption}
              placeholder="Select Alert Manager"
            />
          </Field>

          <Field invalid={!!errors['contact_point']} error={'Contact Point is required'}>
            {isExistingContactPoint ? (
              <Select
                {...register('contact_point', { required: true })}
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
                  setValue('contact_point', value);
                }}
              />
            )}
          </Field> */}
        </div>
      </VerticalGroup>
    </div>
  );

  function onAlertManagerChange(option: SelectableValue<string>) {
    console.log('tralala');

    // const contactPointsForCurrentOption = allContactPoints
    //   .find((opt) => opt.uid === option.value)
    //   .contact_points?.map((cp) => ({ value: cp, label: cp }));

    // const newState: Partial<CustomFieldSectionRendererState> = {
    //   selectedAlertManagerOption: option.value,
    //   contactPoints: contactPointsForCurrentOption,
    // };

    // if (isExistingContactPoint) {
    //   newState.selectedContactPointOption = null;
    //   setValue('contact_point', undefined);
    // }

    // setState(newState);

    // setValue('alert_manager', option.value);
  }

  function onContactPointChange(option: SelectableValue<string>) {
    console.log({ option });

    // setState({ selectedContactPointOption: option.value });
    // setValue('contact_point', option.value);
  }
});

// interface IFormInputs {
//   TextField: string;
//   MyCheckbox: boolean;
// }

// export const HookForm = () => {
//   const { handleSubmit, control, reset } = useForm<IFormInputs>({
//     defaultValues: {
//       MyCheckbox: false,
//     },
//   });
//   const onSubmit: SubmitHandler<IFormInputs> = (data) => console.log(data);

//   return (
//     <form onSubmit={handleSubmit(onSubmit)}>
//       <Controller
//         name="MyCheckbox"
//         control={control}
//         rules={{ required: true }}
//         render={({ field }) => <input type="text" {...field as any} />}
//       />
//       <input type="submit" />
//     </form>
//   );
// };
