import { Tooltip } from '@grafana/ui';
import React, { useEffect, useRef, useState } from 'react';
import cn from 'classnames/bind';

import styles from 'assets/style/utils.css';

const cx = cn.bind(styles);

interface TextEllipsisTooltipProps {
  content: string;
  queryClassName?: string;
  placement?: string;
  className?: string;
  children: JSX.Element | JSX.Element[];
}

/* NOTE: 
   - If you use TextEllipsisTooltip inside rc-table
     you also need to pass `ellipsis: true` to the column to apply truncation
 */

const TextEllipsisTooltip: React.FC<TextEllipsisTooltipProps> = ({
  queryClassName = 'overflow-child',
  className,
  content: textContent,
  placement,
  children,
}) => {
  const [isEllipsis, setIsEllipsis] = useState(true);
  const elContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = elContentRef?.current?.querySelector<HTMLElement>(`.${queryClassName}`);
    if (!el) return;

    setIsEllipsis(el.offsetHeight < el.scrollHeight);
  }, []);

  const elContent = (
    <div className={cx(className)} ref={elContentRef}>
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
};

export default TextEllipsisTooltip;
