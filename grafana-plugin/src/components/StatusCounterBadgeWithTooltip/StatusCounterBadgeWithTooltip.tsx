import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Tooltip, IconName } from '@grafana/ui';
import cn from 'classnames/bind';

import Text, { TextType } from 'components/Text/Text';

import styles from './StatusCounterBadgeWithTooltip.module.scss';

interface StatusCounterBadgeWithTooltipProps {
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

const StatusCounterBadgeWithTooltip: FC<StatusCounterBadgeWithTooltipProps> = (props) => {
  const { type, count, tooltipTitle, tooltipContent, onHover, addPadding } = props;

  return (
    <Tooltip
      placement="bottom-start"
      interactive
      content={
        <div className={cx('tooltip')}>
          <VerticalGroup>
            <Text type="secondary">{tooltipTitle}</Text>
            <Text type="secondary">{tooltipContent}</Text>
          </VerticalGroup>
        </div>
      }
    >
      <div
        className={cx('root', 'element', { [`element--${type}`]: true }, { 'element--padding': addPadding })}
        onMouseEnter={onHover}
      >
        <HorizontalGroup spacing="xs">
          <Icon
            className={cx('element__icon', { [`element__icon--${type}`]: true })}
            name={typeToIcon[type] as IconName}
          />
          <Text className={cx('element__text', { [`element__text--${type}`]: true })}>{count}</Text>
        </HorizontalGroup>
      </div>
    </Tooltip>
  );
};

export default StatusCounterBadgeWithTooltip;
