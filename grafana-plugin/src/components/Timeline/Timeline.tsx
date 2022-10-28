import React from 'react';

import cn from 'classnames/bind';

import TimelineItem, { TimelineItemProps } from './TimelineItem';

import styles from 'components/Timeline/Timeline.module.css';

const cx = cn.bind(styles);

export interface TimelineProps {
  className?: string;
  children?: any;
}

interface TimelineType extends React.FC<TimelineProps> {
  Item: React.FC<TimelineItemProps>;
}

const Timeline: TimelineType = (props) => {
  const { className, children } = props;

  return <ul className={cx('root', className)}>{children}</ul>;
};

Timeline.Item = TimelineItem;

export default Timeline;
