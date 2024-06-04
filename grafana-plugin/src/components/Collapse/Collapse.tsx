import React, { FC, useCallback, useState } from 'react';

import { cx } from '@emotion/css';
import { Icon, useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { getCollapseStyles } from './Collapse.styles';

export interface CollapseProps {
  label: React.ReactNode;
  isOpen: boolean;
  onToggle?: (isOpen: boolean) => void;
  collapsible?: boolean;
  className?: string;
  contentClassName?: string;
  headerWithBackground?: boolean;
  children?: any;
}

export const Collapse: FC<CollapseProps> = (props) => {
  const { label, isOpen: propsIsOpen, onToggle, children, className, contentClassName, headerWithBackground } = props;

  const [stateIsOpen, setStateIsOpen] = useState<boolean>(propsIsOpen);

  const styles = useStyles2(getCollapseStyles);

  const isOpen = onToggle ? propsIsOpen : stateIsOpen;

  const onHeaderClickCallback = useCallback(
    (event) => {
      if (event.target.closest('.no-trigger-collapse-please')) {
        // TODO fix because Grafana's Selects don't support onClick stop propagation
        return;
      }

      if (onToggle) {
        onToggle(!isOpen);
      } else {
        setStateIsOpen(!isOpen);
      }
    },
    [isOpen]
  );

  return (
    <div className={cx(styles.root, className)}>
      <div
        className={cx(styles.header, { [styles.headerWithBackground]: headerWithBackground })}
        onClick={onHeaderClickCallback}
        data-testid="test__toggle"
      >
        <Icon name={'angle-right'} size="xl" className={cx(styles.icon, { [bem(styles.icon, 'rotated')]: isOpen })} />
        <div className={styles.label}> {label}</div>
      </div>
      {isOpen && (
        <div className={cx(styles.content, contentClassName)} data-testid="test__children">
          {children}
        </div>
      )}
    </div>
  );
};
