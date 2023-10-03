import React, { forwardRef, useImperativeHandle, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './Labels.module.css';
import ServiceLabels from 'components/LatestLabelsPicker/components/ServiceLabels/ServiceLabels';

const cx = cn.bind(styles);

interface LabelsProps {
  value: LabelKeyValue[];
  errors: any;
}

const Labels = observer(
  forwardRef(function Labels2(props: LabelsProps, ref) {
    // @ts-ignore
    const { value: defaultValue, errors: propsErrors } = props;

    // @ts-ignore
    const [errors] = useState<[Record<string, any>]>();

    // propsErrors are 'external' caused by attaching/detaching labels to oncall entities,
    // state errors are errors caused by CRUD operations on labels storage

    // @ts-ignore
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

    console.log({ value });

    return (
      <div className={cx('root')}>
        <ServiceLabels
          loadById
          value={value}
          onLoadKeys={labelsStore.loadKeys.bind(labelsStore)}
          onLoadValuesForKey={labelsStore.loadValuesForKey.bind(labelsStore)}
          onCreateKey={labelsStore.createKey.bind(labelsStore)}
          onUpdateKey={labelsStore.updateKey.bind(labelsStore)}
          onCreateValue={labelsStore.createValue.bind(labelsStore)}
          onUpdateValue={labelsStore.updateKeyValue.bind(labelsStore)}
          onRowItemRemoval={(_pair, _index) => {}}
          errors={{ ...propsErrors, ...errors }}
          onDataUpdate={setValue}
        />
      </div>
    );
  })
);

export default Labels;
