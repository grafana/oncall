import React from 'react';

import cn from 'classnames/bind';

import styles from 'components/Timeline/Timeline.module.css';

const cx = cn.bind(styles);

export interface TimelineItemProps {
  className?: string;
  contentClassName?: string;
  isDisabled?: boolean;
  backgroundClassName?: string;
  backgroundHexNumber?: string;
  textColor?: string;
  number?: number;
  badge?: number;
  children?: any;
}

export const TimelineItem: React.FC<TimelineItemProps> = ({
  className,
  contentClassName,
  children,
  isDisabled,
  backgroundClassName,
  backgroundHexNumber,
  textColor = '#ffffff',
  number,
}) => {
  return (
    <li className={cx('item', className)}>
      {!isDisabled && (
        <div
          className={cx('dot', backgroundClassName || '')}
          style={{ backgroundColor: backgroundHexNumber || '', color: textColor }}
        >
          {number}
        </div>
      )}
      <div className={cx('content', contentClassName, { 'content--noMargin': isDisabled })}>{children}</div>
    </li>
  );
};
