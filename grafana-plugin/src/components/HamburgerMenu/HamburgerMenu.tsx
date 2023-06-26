import React, { useRef } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './HamburgerMenu.module.scss';

interface HamburgerMenuProps {
  openMenu: React.MouseEventHandler<HTMLElement>;
  listWidth: number;
  listBorder: number;
  stopPropagation?: boolean;
  withBackground?: boolean;
  className?: string;
}

const cx = cn.bind(styles);

const HamburgerMenu: React.FC<HamburgerMenuProps> = (props) => {
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

export default HamburgerMenu;
