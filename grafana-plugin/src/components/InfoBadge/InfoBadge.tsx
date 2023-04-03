import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Tooltip, IconName } from '@grafana/ui';
import cn from 'classnames/bind';

import Text, { TextType } from 'components/Text/Text';

import styles from './InfoBadge.module.scss';

interface InfoBadgeProps {
  borderType: Partial<TextType>;
  count: number | string;
  tooltipTitle: string;
  tooltipContent: React.ReactNode;

  icon?: string;
  addPadding?: boolean;

  onHover?: () => void;
}

const cx = cn.bind(styles);

const InfoBadge: FC<InfoBadgeProps> = (props) => {
  const { borderType, count, tooltipTitle, tooltipContent, onHover, addPadding, icon } = props;

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
        className={cx('root', 'element', { [`element--${borderType}`]: true }, { 'element--padding': addPadding })}
        onMouseEnter={onHover}
      >
        <HorizontalGroup spacing="xs">
          {icon && (
            <Icon className={cx('element__icon', { [`element__icon--${borderType}`]: true })} name={icon as IconName} />
          )}
          <Text className={cx('element__text', { [`element__text--${borderType}`]: true })}>{count}</Text>
        </HorizontalGroup>
      </div>
    </Tooltip>
  );
};

export default InfoBadge;
