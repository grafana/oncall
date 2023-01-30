import React, { FC, useEffect, useState } from 'react';

import { Tooltip } from '@grafana/ui';
import { debounce } from 'throttle-debounce';

interface MatchMediaTooltipProps {
  placement: 'top' | 'bottom' | 'right' | 'left';
  content: string;
  children: JSX.Element;

  maxWidth?: number;
  minWidth?: number;
}

const DEBOUNCE_MS = 200;

export const MatchMediaTooltip: FC<MatchMediaTooltipProps> = ({ minWidth, maxWidth, placement, content, children }) => {
  const [match, setMatch] = useState<MediaQueryList>(getMatch());

  useEffect(() => {
    const debouncedResize = debounce(DEBOUNCE_MS, onWindowResize);
    window.addEventListener('resize', debouncedResize);
    return () => {
      window.removeEventListener('resize', debouncedResize);
    };
  }, []);

  if (match?.matches) {
    return (
      <Tooltip placement={placement} content={content}>
        {children}
      </Tooltip>
    );
  }

  return <>{children}</>;

  function onWindowResize() {
    setMatch(getMatch());
  }

  function getMatch() {
    if (minWidth && maxWidth) {
      return window.matchMedia(`(min-width: ${minWidth}px) and (max-width: ${maxWidth}px)`);
    } else if (minWidth) {
      return window.matchMedia(`(min-width: ${minWidth}px)`);
    } else if (maxWidth) {
      return window.matchMedia(`(max-width: ${maxWidth}px)`);
    }

    return undefined;
  }
};
