import React from 'react';

import cn from 'classnames/bind';

import styles from 'components/Timeline/Timeline.module.css';

const cx = cn.bind(styles);

export interface TimelineItemProps {
  className?: string;
  contentClassName?: string;
  color?: string;
  number?: number;
  badge?: number;
  children?: any;
}

const TimelineItem: React.FC<TimelineItemProps> = ({
  className,
  contentClassName,
  children,
  color = '#3274D9',
  number,
}) => (
  <li className={cx('item', className)}>
    <div className={cx('dot')} style={{ backgroundColor: color }}>
      {number}
    </div>
    <div className={cx('content', contentClassName)}>{children}</div>
  </li>
);

export default TimelineItem;
