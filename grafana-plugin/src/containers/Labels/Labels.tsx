import React, { forwardRef, useImperativeHandle, useState } from 'react';

// import cn from 'classnames/bind';
import ServiceLabels from 'gops-labels';
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';

// import styles from './Labels.module.css';

// const cx = cn.bind(styles);

interface LabelsProps {}

const Labels = observer(
  forwardRef(function Labels(props: LabelsProps, ref) {
    const {} = props;

    const [value, setValue] = useState([]);

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
      const labels = pairs
        .filter((pair) => Boolean(pair.value))
        .map((pair) => {
          const values = labelsStore.values[pair.id];

          const valueId = values.find((v) => v.repr === pair.value)?.id;

          const label = { key: { id: pair.id, repr: pair.key }, value: { id: valueId, repr: pair.value } };

          return label;
        });

      setValue(labels);
    };

    const onRowItemRemoval = (_pair, rowIndex) => {
      setValue(value.splice(rowIndex, 1));
    };

    return (
      <ServiceLabels
        selectedOptions={[]}
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
