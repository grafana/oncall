import React, { useState, useCallback, ChangeEvent, useEffect } from 'react';

import { VerticalGroup, Icon, Input, RadioButtonGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';

import { EscalationVariantsTab } from './EscalationVariants.types';

import styles from './EscalationVariants.module.css';

const cx = cn.bind(styles);

interface EscalationVariantsProps {
  onHide: () => void;
  tab?: EscalationVariantsTab;
}

const AssignRespondersPicker = (value = { searchTerm: '' }) => {
  const store = useStore();

  const onSearchTermChangeCallback = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const filters = {
        ...value,
        searchTerm: e.currentTarget.value,
      };

      store.scheduleStore.updateItems(filters);
    },
    [value]
  );

  const schedules = store.scheduleStore.getSearchResult();

  return (
    <div className={cx('assign-responders-picker')}>
      <VerticalGroup>
        <Input
          prefix={<Icon name="search" />}
          className={cx('search', 'control')}
          placeholder="Search"
          value={value.searchTerm}
          onChange={onSearchTermChangeCallback}
        />
        <div className={cx('assign-responders-list')}>
          {schedules ? (
            schedules.map((schedule) => <div key={schedule.id}>{schedule.name}</div>)
          ) : (
            <LoadingPlaceholder />
          )}
        </div>
      </VerticalGroup>
    </div>
  );
};

const EscalationVariants = observer(({}: EscalationVariantsProps) => {
  const store = useStore();
  const [activeOption, setActiveOption] = useState('schedules');

  useEffect(() => {
    store.scheduleStore.updateItems('');
  }, []);

  const handleOptionChange = useCallback((option: string) => {
    console.log('OPTION', option);
    setActiveOption(option);
  }, []);

  return (
    <>
      <div className={cx('escalation-variants-dropdown')}>
        <RadioButtonGroup
          options={[
            { value: 'schedules', label: 'Schedules' },
            { value: 'users', label: 'Users' },
          ]}
          value={activeOption}
          onChange={handleOptionChange}
          fullWidth
        />
        <AssignRespondersPicker searchTerm="" />
      </div>
    </>
  );
});

export default EscalationVariants;
