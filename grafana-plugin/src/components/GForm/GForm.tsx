import React from 'react';

import { Field, Form, Input, InputControl, Select, Switch, TextArea } from '@grafana/ui';
import { capitalCase } from 'change-case';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import GSelect from 'containers/GSelect/GSelect';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';

interface GFormProps {
  form: { name: string; fields: FormItem[] };
  data: any;
  onSubmit: (data: any) => void;
}

const nullNormalizer = (value: string) => {
  return value || null;
};

function renderFormControl(formItem: FormItem, register: any, control: any, onChangeFn: (field, value) => void) {
  switch (formItem.type) {
    case FormItemType.Input:
      return (
        <Input {...register(formItem.name, formItem.validation)} onChange={(value) => onChangeFn(undefined, value)} />
      );

    case FormItemType.TextArea:
      return (
        <TextArea
          rows={formItem.extra?.rows || 4}
          {...register(formItem.name, formItem.validation)}
          onChange={(value) => onChangeFn(undefined, value)}
        />
      );

    case FormItemType.MultiSelect:
      return (
        <InputControl
          render={({ field }) => {
            return (
              <GSelect isMulti={true} {...field} {...formItem.extra} onChange={(value) => onChangeFn(field, value)} />
            );
          }}
          control={control}
          name={formItem.name}
        />
      );

    case FormItemType.Select:
      return (
        <InputControl
          render={({ field: { ...field } }) => {
            return <Select {...field} {...formItem.extra} onChange={(value) => onChangeFn(field, value)} />;
          }}
          control={control}
          name={formItem.name}
        />
      );

    case FormItemType.GSelect:
      return (
        <InputControl
          render={({ field: { ...field } }) => {
            return <GSelect {...field} {...formItem.extra} onChange={(value) => onChangeFn(field, value)} />;
          }}
          control={control}
          name={formItem.name}
        />
      );

    case FormItemType.Switch:
      return (
        <Switch {...register(formItem.name, formItem.validation)} onChange={(value) => onChangeFn(undefined, value)} />
      );

    case FormItemType.RemoteSelect:
      return (
        <InputControl
          render={({ field: { ...field } }) => {
            return <RemoteSelect {...field} {...formItem.extra} onChange={(value) => onChangeFn(field, value)} />;
          }}
          control={control}
          name={formItem.name}
        />
      );

    default:
      return null;
  }
}

class GForm extends React.Component<GFormProps, {}> {
  render() {
    const { form, data } = this.props;

    return (
      <Form maxWidth="none" id={form.name} defaultValues={data} onSubmit={this.handleSubmit}>
        {({ register, errors, control, getValues, setValue }) => {
          return form.fields.map((formItem: FormItem, formIndex: number) => {
            if (formItem.isVisible && !formItem.isVisible(getValues())) {
              setValue(formItem.name, undefined); // clear input value on hide
              return null;
            }

            return (
              <Field
                key={formIndex}
                disabled={formItem.getDisabled ? formItem.getDisabled(data) : false}
                label={formItem.label || capitalCase(formItem.name)}
                invalid={!!errors[formItem.name]}
                error={`${capitalCase(formItem.name)} is required`}
                description={formItem.description}
              >
                {renderFormControl(formItem, register, control, (field, value) => {
                  field?.onChange(value);
                  this.forceUpdate();
                })}
              </Field>
            );
          });
        }}
      </Form>
    );
  }

  handleSubmit = (data) => {
    const { form, onSubmit } = this.props;

    const normalizedData = Object.keys(data).reduce((acc, key) => {
      const formItem = form.fields.find((formItem) => formItem.name === key);

      const value = formItem?.normalize ? formItem.normalize(data[key]) : nullNormalizer(data[key]);

      return {
        ...acc,
        [key]: value,
      };
    }, {});

    onSubmit(normalizedData);
  };
}

export default GForm;
