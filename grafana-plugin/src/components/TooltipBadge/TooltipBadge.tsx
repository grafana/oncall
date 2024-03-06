import React, { FC } from 'react';

import { Icon, Tooltip, IconName, VerticalGroup, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import { Text, TextType } from 'components/Text/Text';

import styles from './TooltipBadge.module.scss';

interface TooltipBadgeProps {
  className?: string;
  borderType: Partial<TextType>;
  text?: number | string;
  tooltipContent: React.ReactNode;

  tooltipTitle?: string;
  icon?: IconName;
  customIcon?: React.ReactNode;
  addPadding?: boolean;
  placement?;
  testId?: string;

  onHover?: () => void;
}

const cx = cn.bind(styles);

export const TooltipBadge: FC<TooltipBadgeProps> = (props) => {
  const {
    borderType,
    text,
    tooltipTitle,
    tooltipContent,
    placement,
    onHover,
    addPadding,
    icon,
    customIcon,
    className,
    testId,
  } = props;

  return (
    <Tooltip
      placement={placement || 'bottom-start'}
      interactive
      content={
        <div className={cx('tooltip')}>
          <VerticalGroup spacing="xs">
            <Text type="primary">{tooltipTitle}</Text>
            {tooltipContent && <Text type="secondary">{tooltipContent}</Text>}
          </VerticalGroup>
        </div>
      }
    >
      <div
        className={cx(
          'root',
          'element',
          { [`element--${borderType}`]: true },
          { 'element--padding': addPadding },
          className
        )}
        onMouseEnter={onHover}
        {...(testId ? { 'data-testid': testId } : {})}
      >
        <HorizontalGroup spacing="xs">
          {renderIcon()}
          {text !== undefined && (
            <Text
              className={cx('element__text', { [`element__text--${borderType}`]: true })}
              {...(testId ? { 'data-testid': `${testId}-text` } : {})}
            >
              {text}
            </Text>
          )}
        </HorizontalGroup>
      </div>
    </Tooltip>
  );

  function renderIcon() {
    if (customIcon) {
      return customIcon;
    }
    if (!icon) {
      return null;
    }

    return <Icon className={cx('element__icon', { [`element__icon--${borderType}`]: true })} name={icon as IconName} />;
  }
};
