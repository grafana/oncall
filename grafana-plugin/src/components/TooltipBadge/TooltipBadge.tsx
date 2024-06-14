import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { Icon, Tooltip, IconName, VerticalGroup, HorizontalGroup, useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { Text, TextType } from 'components/Text/Text';

import { getTooltipBadgeStyles } from './TooltipBadge.styles';

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

  const styles = useStyles2(getTooltipBadgeStyles);

  return (
    <Tooltip
      placement={placement || 'bottom-start'}
      interactive
      content={
        <div className={styles.tooltip}>
          <VerticalGroup spacing="xs">
            <Text type="primary">{tooltipTitle}</Text>
            {tooltipContent && <Text type="secondary">{tooltipContent}</Text>}
          </VerticalGroup>
        </div>
      }
    >
      <div
        className={cx(styles.element, styles[borderType], { [bem(styles.element, 'padding')]: addPadding }, className)}
        onMouseEnter={onHover}
        {...(testId ? { 'data-testid': testId } : {})}
      >
        <HorizontalGroup spacing="xs">
          {renderIcon()}
          {text !== undefined && <Text {...(testId ? { 'data-testid': `${testId}-text` } : {})}>{text}</Text>}
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

    return <Icon name={icon as IconName} />;
  }
};
