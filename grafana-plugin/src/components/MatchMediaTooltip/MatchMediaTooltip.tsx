import { Tooltip } from '@grafana/ui';
import React, { FC } from 'react';

interface MediaMatchTooltipProps {
  placement: 'top' | 'bottom' | 'right' | 'left';
  content: string;
  children: JSX.Element;

  maxWidth?: number;
  minWidth?: number;
}

const MediaMatchTooltip: FC<MediaMatchTooltipProps> = ({ minWidth, maxWidth, placement, content, children }) => {
  let match: MediaQueryList;

  if (minWidth && maxWidth) {
    match = window.matchMedia(`(min-width: ${minWidth}px) and (max-width: ${maxWidth}px)`);
  } else if (minWidth) {
    match = window.matchMedia(`(min-width: ${minWidth}px)`);
  } else if (maxWidth) {
    match = window.matchMedia(`(max-width: ${maxWidth}px)`);
  } else {
    return <>{children}</>;
  }

  if (match) {
    return (
      <Tooltip placement={placement} content={content}>
        {children}
      </Tooltip>
    );
  }

  return <>{children}</>;
};

export default MediaMatchTooltip;
