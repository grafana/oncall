import React from 'react';

import { Field, Form, FormFieldErrors, Input, InputControl, Label, Select, Switch, TextArea } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { isEmpty } from 'lodash-es';

import { Collapse } from 'components/Collapse/Collapse';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { Text } from 'components/Text/Text';
import { GSelect } from 'containers/GSelect/GSelect';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';

import styles from './GForm.module.scss';

const cx = cn.bind(styles);

export interface CustomFieldSectionRendererProps {
  control: any;
  formItem: FormItem;
  errors: any;
  register: any;
  setValue: (fieldName: string, fieldValue: any) => void;
  getValues: <T = unknown>(fieldName: string | string[]) => T;
}

interface GFormProps {
  form: { name: string; fields: FormItem[] };
  data: any;
  onSubmit: (data: any) => void;
  onChange?: (formIsValid: boolean) => void;

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

export class GForm extends React.Component<GFormProps, {}> {
  render() {
    const { form, data, onFieldRender, customFieldSectionRenderer: CustomFieldSectionRenderer } = this.props;

    const openFields = form.fields.filter((field) => !field.collapsed);
    const collapsedfields = form.fields.filter((field) => field.collapsed);

    return (
      <Form maxWidth="none" id={form.name} defaultValues={data} onSubmit={this.handleSubmit}>
        {({ register, errors, control, getValues, setValue }) => {
          const renderField = (formItem: FormItem, formIndex: number) => {
            if (this.isFormItemHidden(formItem, getValues())) {
              return null; // don't render the field
            }

            if (formItem.type === FormItemType.PlainLabel) {
              return (
                <Label className={cx('label')}>
                  <Text type="primary">{formItem.label}</Text>
                </Label>
              );
            }

            const disabled = formItem.disabled
              ? true
              : formItem.getDisabled
              ? formItem.getDisabled(getValues())
              : false;

            const formControl = renderFormControl(
              formItem,
              register,
              control,
              disabled,
              this.onChange.bind(this, errors)
            );

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
                  getValues={getValues}
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
                <div className="u-margin-top-xs">
                  {onFieldRender
                    ? onFieldRender(formItem, disabled, formControl, getValues(), (value) =>
                        setValue(formItem.name, value)
                      )
                    : formControl}
                </div>
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

  onChange = (errors: FormFieldErrors, field: any, value: string) => {
    this.props.onChange?.(isEmpty(errors));

    field?.onChange(value);
    this.forceUpdate();
  };

  isFormItemHidden(formItem: FormItem, data) {
    return formItem?.isHidden?.(data);
  }

  handleSubmit = (data) => {
    const { form, onSubmit } = this.props;

    const normalizedData = Object.keys(data).reduce((acc, key) => {
      const formItem = form.fields.find((formItem) => formItem.name === key);

      let value = formItem?.normalize ? formItem.normalize(data[key]) : nullNormalizer(data[key]);

      if (this.isFormItemHidden(formItem, data)) {
        value = undefined;
      }

      return {
        ...acc,
        [key]: value,
      };
    }, {});

    onSubmit(normalizedData);
  };
}
