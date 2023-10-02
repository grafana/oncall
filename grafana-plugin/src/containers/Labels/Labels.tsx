import React, { forwardRef, useImperativeHandle, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import LabelsPicker from 'components/LabelsPicker/LabelsPicker';
import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './Labels.module.css';

const cx = cn.bind(styles);

interface LabelsProps {
  value: LabelKeyValue[];
  errors: any;
}

const Labels = observer(
  forwardRef(function Labels2(props: LabelsProps, ref) {
    const { value: defaultValue, errors: propsErrors } = props;

    const [errors] = useState<[Record<string, any>]>();

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

    return (
      <div className={cx('root')}>
        <LabelsPicker
          errors={{ ...propsErrors, ...errors }}
          value={value}
          labelField="repr"
          valueField="id"
          loadKeys={labelsStore.loadKeys.bind(labelsStore)}
          loadValuesForKey={labelsStore.loadValuesForKey.bind(labelsStore)}
          onChange={setValue}
          createKey={labelsStore.createKey.bind(labelsStore)}
          createValue={labelsStore.createValue.bind(labelsStore)}
          onKeyNameChange={labelsStore.updateKey.bind(labelsStore)}
          onKeyValueNameChange={labelsStore.updateKeyValue.bind(labelsStore)}
        />
      </div>
    );
  })
);

export default Labels;
