import React, { forwardRef, useImperativeHandle, useState } from 'react';

import { ServiceLabelsProps, ServiceLabels } from '@grafana/labels';
import { Field, Label } from '@grafana/ui';
import { isEmpty } from 'lodash-es';
import { observer } from 'mobx-react';

import { splitToGroups } from 'models/label/label.helpers';
import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';
import { GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';

export interface LabelsProps {
  value: LabelKeyValue[];
  errors: any;
  onDataUpdate?: ServiceLabelsProps['onDataUpdate'];
  description?: React.ComponentProps<typeof Label>['description'];
}

const _Labels = observer(
  forwardRef(function Labels2(props: LabelsProps, ref) {
    const { value: defaultValue, errors: propsErrors, onDataUpdate, description } = props;

    // propsErrors are 'external' caused by attaching/detaching labels to oncall entities,
    // state errors are errors caused by CRUD operations on labels storage

    const [value, setValue] = useState<LabelKeyValue[]>(defaultValue);

    const { labelsStore } = useStore();

    const onChange = (value: LabelKeyValue[]) => {
      if (onDataUpdate) {
        onDataUpdate(value);
      }
      setValue(value);
    };

    useImperativeHandle(
      ref,
      () => {
        return {
          getValue() {
            return value;
          },
        };
      },
      [value]
    );

    const onLoadKeys = async (search?: string) => {
      let result = undefined;
      try {
        result = await labelsStore.loadKeys(search);
      } catch (error) {
        openErrorNotification('There was an error processing your request. Please try again');
      }

      const groups = splitToGroups(result);

      return groups;
    };

    const onLoadValuesForKey = async (key: string, search?: string) => {
      let result = undefined;
      try {
        const { values } = await labelsStore.loadValuesForKey(key, search);
        result = values;
      } catch (error) {
        openErrorNotification('There was an error processing your request. Please try again');
      }

      const groups = splitToGroups(result);

      return groups;
    };

    const isValid = () => {
      return (
        (propsErrors || [])
          .map((error: LabelKeyValue, index) => {
            // error object is empty => Valid
            if (isEmpty(error)) {
              return undefined;
            }
            const matchingValue = value[index]?.value;
            // We have a name for the value => Valid
            if (error.value && matchingValue?.name) {
              return undefined;
            }
            const matchingKey = value[index]?.key;
            // We have a name for the key => Valid
            if (error.key && matchingKey?.name) {
              return undefined;
            }
            // Invalid
            return error;
          })
          .filter((er: LabelKeyValue) => er).length === 0
      );
    };

    return (
      <div>
        <Field label={<Label description={<div className="u-padding-vertical-xs">{description}</div>}>Labels</Label>}>
          <ServiceLabels
            loadById
            value={value}
            onLoadKeys={onLoadKeys}
            onLoadValuesForKey={onLoadValuesForKey}
            onCreateKey={labelsStore.createKey}
            onUpdateKey={labelsStore.updateKey}
            onCreateValue={labelsStore.createValue}
            onUpdateValue={labelsStore.updateKeyValue}
            onRowItemRemoval={(_pair, _index) => {}}
            onUpdateError={onUpdateError}
            errors={isValid() ? {} : { ...propsErrors }}
            onDataUpdate={onChange}
            getIsKeyEditable={(option) => !option.prescribed}
            getIsValueEditable={(option) => !option.prescribed}
          />
        </Field>
      </div>
    );
  })
);

function onUpdateError(res) {
  if (res?.response?.status === 409) {
    openErrorNotification(`Duplicate values are not allowed`);
  } else {
    openErrorNotification(GENERIC_ERROR);
  }
}

export const Labels = React.memo(_Labels);
