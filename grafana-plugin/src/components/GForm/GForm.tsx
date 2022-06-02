import React, { useCallback } from 'react';

import { Field, Form, Input, InputControl, Select, Switch, TextArea } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import GSelect from 'containers/GSelect/GSelect';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';

import styles from './GForm.module.css';

interface GFormProps {
  form: { name: string; fields: FormItem[] };
  data: any;
  /* errors: { [key: string]: string }; */
  onSubmit: (data: any) => void;
}

const nullNormalizer = (value: string) => {
  return value || null;
};

const cx = cn.bind(styles);

function renderFormControl(formItem: FormItem, register: any, control: any) {
  switch (formItem.type) {
    case FormItemType.Input:
      return <Input {...register(formItem.name, formItem.validation)} />;

    case FormItemType.TextArea:
      return <TextArea rows={formItem.extra?.rows || 4} {...register(formItem.name, formItem.validation)} />;

    case FormItemType.Select:
      return (
        <InputControl
          render={({ field: { onChange, ...field } }) => {
            return <Select {...field} {...formItem.extra} onChange={(value) => onChange(value.value)} />;
          }}
          control={control}
          // @ts-ignore
          name={formItem.name}
        />
      );

    case FormItemType.GSelect:
      return (
        <InputControl
          render={({ field: { ...field } }) => {
            return <GSelect {...field} {...formItem.extra} />;
          }}
          control={control}
          // @ts-ignore
          name={formItem.name}
        />
      );

    case FormItemType.Switch:
      return <Switch {...register(formItem.name, formItem.validation)} />;

    case FormItemType.RemoteSelect:
      return (
        <InputControl
          render={({ field: { ...field } }) => {
            return <RemoteSelect {...field} {...formItem.extra} />;
          }}
          control={control}
          // @ts-ignore
          name={formItem.name}
        />
      );

    default:
      return null;
  }
}

const GForm = (props: GFormProps) => {
  const { data, form, onSubmit } = props;

  const handleSubmit = useCallback(
    (data: any) => {
      const normalizedData = Object.keys(data).reduce((acc, key) => {
        const formItem = form.fields.find((formItem) => formItem.name === key);

        const value = formItem?.normalize ? formItem.normalize(data[key]) : nullNormalizer(data[key]);

        return {
          ...acc,
          [key]: value,
        };
      }, {});

      onSubmit(normalizedData);
    },
    [onSubmit]
  );

  return (
    <Form maxWidth="none" id={form.name} defaultValues={data} onSubmit={handleSubmit}>
      {({ register, errors, control }) => {
        return form.fields.map((formItem: FormItem) => {
          return (
            <Field
              disabled={formItem.getDisabled ? formItem.getDisabled(data) : false}
              label={formItem.label || capitalCase(formItem.name)}
              invalid={!!errors[formItem.name]}
              error={`${capitalCase(formItem.name)} is required`}
              description={formItem.description}
            >
              {renderFormControl(formItem, register, control)}
            </Field>
          );
        });
      }}
    </Form>
  );
};

export default GForm;
