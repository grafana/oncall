import React, { forwardRef, useCallback, useImperativeHandle, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './Labels.module.css';

import ServiceLabels from '@grafana/labels';
import '@grafana/labels/dist/theme.css';

import { openErrorNotification } from 'utils';
import { Field } from '@grafana/ui';

const cx = cn.bind(styles);

interface LabelsProps {
  value: LabelKeyValue[];
  errors: any;
}

const Labels = observer(
  forwardRef(function Labels2(props: LabelsProps, ref) {
    const { value: defaultValue, errors: propsErrors } = props;

    // propsErrors are 'external' caused by attaching/detaching labels to oncall entities,
    // state errors are errors caused by CRUD operations on labels storage

    const [value, setValue] = useState<LabelKeyValue[]>(defaultValue);

    const { labelsStore } = useStore();

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

    const cachedOnLoadKeys = useCallback(() => {
      let result = undefined;
      return async (search?: string) => {
        if (!result) {
          result = await labelsStore.loadKeys();
        }

        return result.filter((k) => k.repr.toLowerCase().includes(search.toLowerCase()));
      };
    }, []);

    const cachedOnLoadValuesForKey = useCallback(() => {
      let result = undefined;
      return async (key: string, search?: string) => {
        if (!result) {
          result = await labelsStore.loadValuesForKey(key, search);
        }

        return result.filter((k) => k.repr.toLowerCase().includes(search.toLowerCase()));
      };
    }, []);

    return (
      <div className={cx('root')}>
        <Field label="Labels">
          <ServiceLabels
            loadById
            value={value}
            onLoadKeys={cachedOnLoadKeys()}
            onLoadValuesForKey={cachedOnLoadValuesForKey()}
            onCreateKey={labelsStore.createKey.bind(labelsStore)}
            onUpdateKey={labelsStore.updateKey.bind(labelsStore)}
            onCreateValue={labelsStore.createValue.bind(labelsStore)}
            onUpdateValue={labelsStore.updateKeyValue.bind(labelsStore)}
            onRowItemRemoval={(_pair, _index) => {}}
            onUpdateError={onUpdateError}
            errors={{ ...propsErrors }}
            onDataUpdate={setValue}
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
    openErrorNotification('An error has occurred. Please try again');
  }
}

export default Labels;
