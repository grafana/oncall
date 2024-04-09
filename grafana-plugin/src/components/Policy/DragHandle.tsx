import React from 'react';

import { cx } from '@emotion/css';
import { Icon, useStyles2 } from '@grafana/ui';
import { SortableHandle } from 'react-sortable-hoc';
import { bem } from 'styles/utils.styles';

import { getPolicyStyles } from './Policy.styles';

const _DragHandle = ({ disabled }: { disabled?: boolean }) => {
  const styles = useStyles2(getPolicyStyles);

  return (
    <div className={cx(styles.control, styles.handle, { [bem(styles.handle, 'disabled')]: disabled })}>
      <Icon name="draggabledots" />
    </div>
  );
};

export const DragHandle = SortableHandle(_DragHandle);
