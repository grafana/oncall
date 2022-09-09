import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';

import styles from './SchedulesFilters.module.css';

const cx = cn.bind(styles);

interface SchedulesFiltersProps {}

const SchedulesFilters = observer((props: SchedulesFiltersProps) => {
  const {} = props;

  const store = useStore();

  const {} = store;

  return <div className={cx('root')} />;
});

export default SchedulesFilters;
