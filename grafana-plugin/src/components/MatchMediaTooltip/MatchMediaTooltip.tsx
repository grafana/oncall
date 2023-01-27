import React, { FC } from 'react';

import { Tooltip } from '@grafana/ui';

interface MediaMatchTooltipProps {
  placement: 'top' | 'bottom' | 'right' | 'left';
  content: string;
  children: JSX.Element;

  maxWidth?: number;
  minWidth?: number;
}

export const MatchMediaTooltip: FC<MediaMatchTooltipProps> = ({ minWidth, maxWidth, placement, content, children }) => {
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

  if (match.matches) {
    return (
      <Tooltip placement={placement} content={content}>
        {children}
      </Tooltip>
    );
  }

  return <>{children}</>;
};
