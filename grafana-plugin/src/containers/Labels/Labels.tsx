/* import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from 'react';

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

    const [allOptions, setAllOptions] = useState();
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

    const fetchAllOptions = useCallback(async () => {
      const keys = await labelsStore.updateKeys();

      const allOptions = keys.reduce((memo, key) => {
        memo[key.repr] = { id: key.id, values: [] };
        return memo;
      }, {});

      const promises = value.map((value) =>
        labelsStore
          .getValuesForKey(value.key.id)
          .then(({ values }) => (allOptions[value.key.repr].values = values.map((v) => ({ id: v.id, value: v.repr }))))
      );

      await Promise.all(promises);

      return allOptions;
    }, [value]);

    useEffect(() => {
      fetchAllOptions().then(setAllOptions);
    }, []);

    const loadLabelsForKeys = async (repr: string) => {
      const keyId = labelsStore.keys.find((key) => key.repr === repr).id;
      const response = await labelsStore.getValuesForKey(keyId);

      const result = response.values.map((value) => ({ id: value.id, value: value.repr }));

      return result;
    };

    const onNewKeyAdd = (key: string) => {
      labelsStore.createKey(key);
    };

    const onNewValueAdd = async (repr, value) => {
      const key = labelsStore.keys.find((key) => key.repr === repr);

      const { values } = await labelsStore.addValue(key.id, value);

      setAllOptions((allOptions) => ({
        ...allOptions,
        [key.repr]: {
          ...allOptions[key.repr],
          values,
        },
      }));

      const newValues = [...values];

      const value = newValues.find((v) => v.key.id === key.id);
      value.value.id;
    };

    const onUpdate = (pairs) => {
      console.log('pairs', pairs);
      setValue(pairs);
    };

    const onRowItemRemoval = (_pair, rowIndex) => {
      console.log(rowIndex);
      setValue([...value.splice(rowIndex, 1)]);
    };

    console.log(allOptions);

    if (!allOptions) {
      return undefined;
    }

    return (
      <ServiceLabels
        selectedOptions={value}
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
 */
