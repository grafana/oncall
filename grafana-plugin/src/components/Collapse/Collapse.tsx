import React, { FC, useCallback, useState } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';

import styles from 'components/Collapse/Collapse.module.css';

interface CollapseProps {
  label: React.ReactNode;
  isOpen: boolean;
  onToggle?: (isOpen: boolean) => void;
  collapsible?: boolean;
  className?: string;
  contentClassName?: string;
  headerWithBackground?: boolean;
  children?: any
}

const cx = cn.bind(styles);

const Collapse: FC<CollapseProps> = (props) => {
  const { label, isOpen: propsIsOpen, onToggle, children, className, contentClassName, headerWithBackground } = props;

  const [stateIsOpen, setStateIsOpen] = useState<boolean>(propsIsOpen);

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
    <div className={cx('root', className)}>
      <div className={cx('header', { 'header_with-background': headerWithBackground })} onClick={onHeaderClickCallback}>
        <Icon name={isOpen ? 'angle-down' : 'angle-right'} size="xl" className={cx('icon')} />
        <div className={cx('label')}> {label}</div>
      </div>
      {isOpen && <div className={cx('content', contentClassName)}>{children}</div>}
    </div>
  );
};

export default Collapse;
