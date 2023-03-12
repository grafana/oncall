import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Tooltip, IconName } from '@grafana/ui';
import cn from 'classnames/bind';

import Text, { TextType } from 'components/Text/Text';

import styles from './ScheduleCounter.module.css';

interface ScheduleCounterProps {
  type: Partial<TextType>;
  count: number;
  tooltipTitle: string;
  tooltipContent: React.ReactNode;
  addPadding?: boolean;
  onHover?: () => void;
}

const typeToIcon = {
  link: 'link',
  warning: 'exclamation-triangle',
};

const cx = cn.bind(styles);

const ScheduleCounter: FC<ScheduleCounterProps> = (props) => {
  const { type, count, tooltipTitle, tooltipContent, onHover, addPadding } = props;

  return (
    <Tooltip
      placement="bottom-start"
      interactive
      content={
        <div className={cx('tooltip', { [`tooltip__type_${type}`]: true })}>
          <VerticalGroup>
            <Text type="secondary">{tooltipTitle}</Text>
            <Text type="secondary">{tooltipContent}</Text>
          </VerticalGroup>
        </div>
      }
    >
      <div className={cx('root', { [`root__type_${type}`]: true }, { padding: addPadding })} onMouseEnter={onHover}>
        <HorizontalGroup spacing="xs">
          <Icon className={cx('icon', { [`icon__type_${type}`]: true })} name={typeToIcon[type] as IconName} />
          <Text className={cx('text', { [`text__type_${type}`]: true })}>{count}</Text>
        </HorizontalGroup>
      </div>
    </Tooltip>
  );
};

export default ScheduleCounter;
