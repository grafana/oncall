import React from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

import { getTimelineStyles } from './Timeline.styles';
import { TimelineItem, TimelineItemProps } from './TimelineItem';

export interface TimelineProps {
  className?: string;
  children?: any;
}

interface TimelineType extends React.FC<TimelineProps> {
  Item: React.FC<TimelineItemProps>;
}

export const Timeline: TimelineType = (props) => {
  const { className, children } = props;
  const styles = useStyles2(getTimelineStyles);

  return <ul className={cx(styles.root, className)}>{children}</ul>;
};

Timeline.Item = TimelineItem;
