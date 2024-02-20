import React from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { SortableHandle } from 'react-sortable-hoc';

import styles from './Policy.module.css';

const cx = cn.bind(styles);

const _DragHandle = ({ disabled }: { disabled?: boolean }) => (
  <div className={cx('control', 'handle', { handle_disabled: disabled })}>
    <Icon name="draggabledots" />
  </div>
);

export const DragHandle = SortableHandle(_DragHandle);
