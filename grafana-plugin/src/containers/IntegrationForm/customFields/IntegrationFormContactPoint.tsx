import React, { FC, useEffect, useReducer } from 'react';

import { SelectableValue } from '@grafana/data';
import { VerticalGroup, HorizontalGroup, Input, RadioButtonGroup, Select, Icon, Label, Field } from '@grafana/ui';
import cn from 'classnames/bind';

import { CustomFieldSectionRendererProps } from 'components/GForm/GForm';
import styles from 'containers/IntegrationForm/IntegrationForm.module.scss';
import { IntegrationFormFieldName } from 'containers/IntegrationForm/IntegrationForm.types';
import { useStore } from 'state/useStore';

const cx = cn.bind(styles);

interface IntegrationFormContactPointProps extends CustomFieldSectionRendererProps {}

interface CustomFieldSectionRendererState {
  isExistingContactPoint: boolean;
  selectedAlertManagerOption: string;
  selectedContactPointOption: string;

  dataSources: Array<{ label: string; value: string }>;
  contactPoints: Array<{ label: string; value: string }>;
  allContactPoints: Array<{ name: string; uid: string; contact_points: string[] }>;
}

const IntegrationFormContactPoint: FC<IntegrationFormContactPointProps> = ({ errors, register, setValue }) => {
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
    (state: CustomFieldSectionRendererState, newState: Partial<CustomFieldSectionRendererState>) => ({
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

  const { alertReceiveChannelStore } = useStore();

  useEffect(() => {
    (async function () {
      const response = await alertReceiveChannelStore.getGrafanaAlertingContactPoints();
      setState({
        allContactPoints: response,
        dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
        contactPoints: [],
      });
    })();

    setValue(IntegrationFormFieldName.IsExisting, true);
  }, []);

  return (
    <div className={cx('extra-fields')}>
      <VerticalGroup spacing="md">
        <HorizontalGroup spacing="xs" align="center">
          <Label>Grafana Alerting Contact point</Label>
          <Icon name="info-circle" className={cx('extra-fields__icon')} />
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

              setValue(IntegrationFormFieldName.IsExisting, radioValue === 'existing');
              setValue(IntegrationFormFieldName.AlertManager, undefined);
              setValue(IntegrationFormFieldName.ContactPoint, undefined);
            }}
          />
        </div>

        <div className={cx('selectors-container')}>
          <Field invalid={!!errors[IntegrationFormFieldName.AlertManager]} error={'Alert Manager is required'}>
            <Select
              {...register(IntegrationFormFieldName.AlertManager, { required: true })}
              options={dataSources}
              onChange={onAlertManagerChange}
              value={selectedAlertManagerOption}
              placeholder="Select Alert Manager"
            />
          </Field>

          <Field invalid={!!errors[IntegrationFormFieldName.ContactPoint]} error={'Contact Point is required'}>
            {isExistingContactPoint ? (
              <Select
                {...register(IntegrationFormFieldName.ContactPoint, { required: true })}
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
                  setValue(IntegrationFormFieldName.ContactPoint, value);
                }}
              />
            )}
          </Field>
        </div>
      </VerticalGroup>
    </div>
  );

  function onAlertManagerChange(option: SelectableValue<string>) {
    const contactPointsForCurrentOption = allContactPoints
      .find((opt) => opt.uid === option.value)
      .contact_points?.map((cp) => ({ value: cp, label: cp }));

    const newState: Partial<CustomFieldSectionRendererState> = {
      selectedAlertManagerOption: option.value,
      contactPoints: contactPointsForCurrentOption,
    };

    if (isExistingContactPoint) {
      newState.selectedContactPointOption = null;
      setValue(IntegrationFormFieldName.ContactPoint, undefined);
    }

    setState(newState);

    setValue(IntegrationFormFieldName.AlertManager, option.value);
  }

  function onContactPointChange(option: SelectableValue<string>) {
    setState({ selectedContactPointOption: option.value });
    setValue(IntegrationFormFieldName.ContactPoint, option.value);
  }
};

export default IntegrationFormContactPoint;
