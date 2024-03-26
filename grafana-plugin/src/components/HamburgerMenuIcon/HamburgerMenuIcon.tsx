import React, { useRef } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './HamburgerMenuIcon.module.scss';

interface HamburgerMenuIconProps {
  openMenu: React.MouseEventHandler<HTMLElement>;
  listWidth: number;
  listBorder: number;
  stopPropagation?: boolean;
  withBackground?: boolean;
  className?: string;
}

const cx = cn.bind(styles);

export const HamburgerMenuIcon: React.FC<HamburgerMenuIconProps> = (props) => {
  const ref = useRef<HTMLDivElement>();
  const { openMenu, listBorder, listWidth, withBackground, className, stopPropagation = false } = props;
  return (
    <div
      ref={ref}
      className={cx('hamburgerMenu', { 'hamburgerMenu--withBackground': withBackground }, className)}
      onClick={(e) => {
        if (stopPropagation) {
          e.stopPropagation();
        }

        const boundingRect = ref.current.getBoundingClientRect();

        openMenu({
          pageX: boundingRect.right - listWidth + listBorder * 2,
          pageY: boundingRect.top + boundingRect.height,
        } as any);
      }}
    >
      <Icon size="sm" name="ellipsis-v" />
    </div>
  );
};
