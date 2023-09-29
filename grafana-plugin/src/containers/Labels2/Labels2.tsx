import React, { forwardRef, useImperativeHandle, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import LabelsPicker from 'components/LabelsPicker/LabelsPicker';
import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './Labels2.module.css';

const cx = cn.bind(styles);

interface Labels2Props {
  value: LabelKeyValue[];
}

const Labels2 = observer(
  forwardRef(function Labels2(props: Labels2Props, ref) {
    const { value: defaultValue } = props;

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

export default Labels2;
