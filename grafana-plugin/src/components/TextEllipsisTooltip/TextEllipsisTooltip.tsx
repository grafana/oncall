import React, { ReactElement, useEffect, useRef, useState } from 'react';

import { cx } from '@emotion/css';
import { Tooltip } from '@grafana/ui';
import { TEXT_ELLIPSIS_CLASS } from 'helpers/consts';

interface TextEllipsisTooltipProps {
  content?: string;
  placement?: string;
  className?: string;
  children: ReactElement | ReactElement[];
}

export const TextEllipsisTooltip: React.FC<TextEllipsisTooltipProps> = ({
  className,
  content: textContent,
  placement,
  children,
}) => {
  const [isEllipsis, setIsEllipsis] = useState(false);
  const elContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setEllipsis();
  }, []);

  const elContent = (
    <div className={cx(className)} ref={elContentRef} onMouseOver={setEllipsis}>
      {children}
    </div>
  );

  if (isEllipsis) {
    return (
      <Tooltip content={textContent} placement={placement as any}>
        {/* The wrapping div is needed, otherwise the attached ref will be lost when <Tooltip /> mounts */}
        <div>{elContent}</div>
      </Tooltip>
    );
  }

  return elContent;

  function setEllipsis() {
    let el = elContentRef?.current?.querySelector<HTMLElement>(`.${TEXT_ELLIPSIS_CLASS}`);
    if (!el) {
      return;
    }

    setIsEllipsis(el.offsetHeight < el.scrollHeight);
  }
};
