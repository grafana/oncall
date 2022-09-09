import React, { FC } from 'react';

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

const TimelineItem: React.FC<TimelineItemProps> = (props) => {
  const { className, contentClassName, children, color = '#3274D9', number } = props;

  const style = { backgroundColor: color };

  return (
    <li className={cx('item', className)}>
      {/*<Badge count={badge} style={style} showZero={false}>*/}
      <div className={cx('dot')} style={{ backgroundColor: color }}>
        {number}
      </div>
      {/*</Badge>*/}
      <div className={cx('content', contentClassName)}>{children}</div>
    </li>
  );
};

export default TimelineItem;
