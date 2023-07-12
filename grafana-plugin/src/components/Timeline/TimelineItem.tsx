import React from 'react';

import cn from 'classnames/bind';

import styles from 'components/Timeline/Timeline.module.css';

const cx = cn.bind(styles);

export interface TimelineItemProps {
  className?: string;
  contentClassName?: string;
  isDisabled?: boolean;
  backgroundColor?: string;
  textColor?: string;
  number?: number;
  badge?: number;
  children?: any;
}

const TimelineItem: React.FC<TimelineItemProps> = ({
  className,
  contentClassName,
  children,
  isDisabled,
  backgroundColor = '#3274D9',
  textColor = '#ffffff',
  number,
}) => {
  return (
    <li className={cx('item', className)}>
      {!isDisabled && (
        <div className={cx('dot')} style={{ backgroundColor, color: textColor }}>
          {number}
        </div>
      )}
      <div className={cx('content', contentClassName, { 'content--noMargin': isDisabled })}>{children}</div>
    </li>
  );
};

export default TimelineItem;
