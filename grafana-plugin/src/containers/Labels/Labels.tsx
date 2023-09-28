import React, { forwardRef, useImperativeHandle, useMemo, useState } from 'react';

// import cn from 'classnames/bind';
import ServiceLabels from '@grafana/labels';
import '@grafana/labels/dist/theme.css';
import { observer } from 'mobx-react';

import { LabelKeyValue } from 'models/label/label.types';
import { useStore } from 'state/useStore';

// import styles from './Labels.module.css';

// const cx = cn.bind(styles);

interface LabelsProps {
  value: LabelKeyValue[];
}

const Labels = observer(
  forwardRef(function Labels(props: LabelsProps, ref) {
    const { value: defaultValue } = props;

    const [value, setValue] = useState(defaultValue);

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

    const selectedOptions = useMemo(() => {
      return value.map((v) => ({ id: v.value.id, key: v.key.repr, value: v.value.repr }));
    }, [value]);

    const allOptions = labelsStore.keys.reduce((memo, key) => {
      memo[key.repr] = { id: key.id, values: [] };
      return memo;
    }, {});

    const loadLabelsForKeys = async (repr: string) => {
      const keyId = labelsStore.keys.find((key) => key.repr === repr).id;
      const response = await labelsStore.getValuesForKey(keyId);

      return response.values.map((value) => ({ id: value.id, value: value.repr }));
    };

    const onNewKeyAdd = (key: string) => {
      labelsStore.createKey(key);
    };

    const onNewValueAdd = (repr, value) => {
      const keyId = labelsStore.keys.find((key) => key.repr === repr).id;
      labelsStore.addValue(keyId, value);
    };

    const onUpdate = (pairs) => {
      setValue(pairs);
    };

    const onRowItemRemoval = (_pair, rowIndex) => {
      console.log(rowIndex);
      setValue([...value.splice(rowIndex, 1)]);
    };

    console.log('selectedOptions', selectedOptions);
    console.log('allOptions', allOptions);

    return (
      <ServiceLabels
        selectedOptions={selectedOptions}
        allOptions={allOptions}
        onNewKeyAdd={onNewKeyAdd}
        onRowItemRemoval={onRowItemRemoval}
        onUpdate={onUpdate}
        onNewValueAdd={onNewValueAdd}
        loadLabelsForKeys={loadLabelsForKeys}
      />
    );
  })
);

Labels.displayName = 'Labels';

export default Labels;
