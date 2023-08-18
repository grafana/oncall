import React from 'react';

import { Field, Form, Input, InputControl, Select, Switch, TextArea } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';

import Collapse from 'components/Collapse/Collapse';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import GSelect from 'containers/GSelect/GSelect';
import { CustomFieldSectionRendererProps } from 'containers/IntegrationForm/IntegrationForm';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';

import styles from './GForm.module.scss';

const cx = cn.bind(styles);

interface GFormProps {
  form: { name: string; fields: FormItem[] };
  data: any;
  onSubmit: (data: any) => void;

  customFieldSectionRenderer?: React.FC<CustomFieldSectionRendererProps>;
  onFieldRender?: (
    formItem: FormItem,
    disabled: boolean,
    renderedControl: React.ReactElement,
    values: any,
    setValue: (value: string) => void
  ) => React.ReactElement;
}

const nullNormalizer = (value: string) => {
  return value || null;
};

function renderFormControl(
  formItem: FormItem,
  register: any,
  control: any,
  disabled: boolean,
  onChangeFn: (field, value) => void
) {
  switch (formItem.type) {
    case FormItemType.Input:
      return (
        <Input
          {...register(formItem.name, formItem.validation)}
          placeholder={formItem.placeholder}
          onChange={(value) => onChangeFn(undefined, value)}
        />
      );

    case FormItemType.Password:
      return (
        <Input
          {...register(formItem.name, formItem.validation)}
          placeholder={formItem.placeholder}
          type="password"
          onChange={(value) => onChangeFn(undefined, value)}
        />
      );

    case FormItemType.TextArea:
      return (
        <TextArea
          rows={formItem.extra?.rows || 4}
          placeholder={formItem.placeholder}
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
            return (
              <Select
                {...field}
                {...formItem.extra}
                {...register(formItem.name, formItem.validation)}
                onChange={(value) => onChangeFn(field, value.value)}
              />
            );
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
        <InputControl
          render={({ field: { ...field } }) => {
            return (
              <Switch
                {...register(formItem.name, formItem.validation)}
                onChange={(value) => onChangeFn(field, value)}
              />
            );
          }}
          control={control}
          name={formItem.name}
        />
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

    case FormItemType.Monaco:
      return (
        <InputControl
          control={control}
          name={formItem.name}
          render={({ field: { ...field } }) => {
            return (
              <MonacoEditor
                {...field}
                {...formItem.extra}
                showLineNumbers={false}
                monacoOptions={{
                  ...MONACO_READONLY_CONFIG,
                  readOnly: disabled,
                }}
                onChange={(value) => onChangeFn(field, value)}
              />
            );
          }}
        />
      );

    default:
      return null;
  }
}

class GForm extends React.Component<GFormProps, {}> {
  render() {
    const { form, data, onFieldRender, customFieldSectionRenderer: CustomFieldSectionRenderer } = this.props;

    const openFields = form.fields.filter((field) => !field.collapsed);
    const collapsedfields = form.fields.filter((field) => field.collapsed);

    return (
      <Form maxWidth="none" id={form.name} defaultValues={data} onSubmit={this.handleSubmit}>
        {({ register, errors, control, getValues, setValue }) => {
          const renderField = (formItem: FormItem, formIndex: number) => {
            if (formItem.isVisible && !formItem.isVisible(getValues())) {
              setValue(formItem.name, undefined); // clear input value on hide
              return null;
            }

            const disabled = formItem.disabled
              ? true
              : formItem.getDisabled
              ? formItem.getDisabled(getValues())
              : false;

            const formControl = renderFormControl(formItem, register, control, disabled, this.onChange);

            if (CustomFieldSectionRenderer && formItem.type === FormItemType.Other && formItem.render) {
              return (
                <CustomFieldSectionRenderer
                  control={control}
                  formItem={formItem}
                  setValue={(fName: string, fValue: any) => {
                    setValue(fName, fValue);
                    this.forceUpdate();
                  }}
                  errors={errors}
                  register={register}
                />
              );
            }

            // skip input render when there's no Custom Renderer
            if (formItem.type === FormItemType.Other) {
              return undefined;
            }

            return (
              <Field
                key={formIndex}
                disabled={disabled}
                label={formItem.label || capitalCase(formItem.name)}
                invalid={!!errors[formItem.name]}
                error={formItem.label ? `${formItem.label} is required` : `${capitalCase(formItem.name)} is required`}
                description={formItem.description}
              >
                {onFieldRender
                  ? onFieldRender(formItem, disabled, formControl, getValues(), (value) =>
                      setValue(formItem.name, value)
                    )
                  : formControl}
              </Field>
            );
          };

          return (
            <>
              {openFields.map(renderField)}
              {collapsedfields.length > 0 && (
                <Collapse isOpen={false} label="Notification settings" className={cx('collapse')}>
                  {collapsedfields.map(renderField)}
                </Collapse>
              )}
            </>
          );
        }}
      </Form>
    );
  }

  onChange = (field: any, value: string) => {
    field?.onChange(value);
    this.forceUpdate();
  };

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
