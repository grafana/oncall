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

    setIsEllipsis(el.offsetWidth < el.scrollWidth);
  }, [elContentRef?.current]);

  const elContent = (
    <div>
      {/* Seems React has a problem setting ref if we don't pass a wrapping element */}
      <div className={cx(className, 'overflow-parent')} ref={elContentRef}>
        {children}
      </div>
    </div>
  );

  if (isEllipsis) {
    return (
      <Tooltip content={textContent} placement={placement as any}>
        {elContent}
      </Tooltip>
    );
  }

  return elContent;
};

export default TextEllipsisTooltip;
